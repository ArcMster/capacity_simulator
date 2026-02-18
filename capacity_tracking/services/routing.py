import datetime
from django.db.models import Prefetch
from ..models import VesselSchedule, PortOfCall, Port
from collections import deque

class RouteFinderService:
    def __init__(self, max_legs=4, min_connection_hours=4):
        self.max_legs = max_legs
        self.min_connection_hours = min_connection_hours

    def find_routes(self, from_port_id, to_port_id, start_date=None, limit=100):
        """
        High-performance route finder using BFS and in-memory graph.
        """
        from_port_id = int(from_port_id)
        to_port_id = int(to_port_id)
        
        if isinstance(start_date, str):
            try:
                # Handle ISO format with 'Z' or offset
                start_date = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                start_date = None

        # 1. Bulk Load Data
        # We load all active schedules and their port calls to avoid per-step queries.
        schedules_qs = VesselSchedule.objects.select_related('vessel', 'service').prefetch_related(
            Prefetch('port_of_calls', queryset=PortOfCall.objects.select_related('port').order_by('port_order'))
        )
        
        # Build in-memory lookup: port_id -> list of (schedule, start_pc_idx)
        # and next_schedule lookup: schedule_id -> list of next_schedules
        port_to_schedules = {}
        schedule_map = {} # id -> schedule object
        next_schedules = {} # prev_id -> list of next_schedules
        
        for s in schedules_qs:
            schedule_map[s.id] = s
            if s.previous_schedule_id:
                if s.previous_schedule_id not in next_schedules:
                    next_schedules[s.previous_schedule_id] = []
                next_schedules[s.previous_schedule_id].append(s)
            
            pcs = list(s.port_of_calls.all())
            for idx, pc in enumerate(pcs):
                if pc.port_id not in port_to_schedules:
                    port_to_schedules[pc.port_id] = []
                port_to_schedules[pc.port_id].append((s, idx))

        # 2. BFS Search
        # Queue stores (current_port_id, current_path, latest_known_date)
        queue = deque([(from_port_id, [], start_date)])
        all_found_routes = []

        while queue:
            curr_port, path, latest_known_date = queue.popleft()

            if len(path) >= self.max_legs:
                continue

            # Find schedules departing from current port
            potential_legs = port_to_schedules.get(curr_port, [])
            
            for s, start_idx in potential_legs:
                # Avoid using the same schedule twice in a route
                used_schedule_ids = set()
                for leg in path:
                    for s_id in leg['schedule_ids']:
                        used_schedule_ids.add(s_id)
                if s.id in used_schedule_ids:
                    continue
                
                pcs = list(s.port_of_calls.all())
                start_pc = pcs[start_idx]
                
                # --- Chronological Pruning ---
                effective_floor = latest_known_date
                if path and latest_known_date:
                    effective_floor = latest_known_date + datetime.timedelta(hours=self.min_connection_hours)

                if effective_floor:
                    if start_pc.etd and start_pc.etd < effective_floor - datetime.timedelta(hours=24):
                        continue
                    elif not start_pc.etd:
                        first_known_after = next((pc.eta or pc.etd for pc in pcs[start_idx+1:] if pc.eta or pc.etd), None)
                        if first_known_after and first_known_after < effective_floor:
                            continue

                # --- Voyage Chaining: BFS for destinations within a leg ---
                # A single leg can span multiple linked schedules of the SAME vessel.
                internal_queue = deque([(s, start_idx, [s.id])])
                
                while internal_queue:
                    curr_s, curr_idx, leg_schedules_ids = internal_queue.popleft()
                    curr_pcs = list(curr_s.port_of_calls.all())
                    
                    # Explore ports in the current schedule
                    for next_idx in range(curr_idx + 1, len(curr_pcs)):
                        next_pc = curr_pcs[next_idx]
                        
                        # Validation for this port
                        if effective_floor:
                            if next_pc.eta and next_pc.eta < effective_floor:
                                continue
                            elif not next_pc.eta and next_pc.etd and next_pc.etd < effective_floor:
                                continue

                        current_leg_latest = latest_known_date
                        dates_in_leg = [d for d in [start_pc.eta, start_pc.etd, next_pc.eta, next_pc.etd] if d]
                        if dates_in_leg:
                            current_leg_latest = max(current_leg_latest or dates_in_leg[0], max(dates_in_leg))

                        new_leg = {
                            'schedule_ids': leg_schedules_ids,
                            'pol_pc': start_pc,
                            'pod_pc': next_pc,
                            'latest_date': current_leg_latest
                        }
                        new_path = path + [new_leg]

                        if next_pc.port_id == to_port_id:
                            # Found a complete route!
                            pol_leg = new_path[0]
                            pod_leg = new_path[-1]
                            duration = None
                            if pol_leg['pol_pc'].etd and pod_leg['pod_pc'].eta:
                                duration = (pod_leg['pod_pc'].eta - pol_leg['pol_pc'].etd).total_seconds() / (24 * 3600)
                            elif pol_leg['pol_pc'].eta and pod_leg['pod_pc'].eta:
                                duration = (pod_leg['pod_pc'].eta - pol_leg['pol_pc'].eta).total_seconds() / (24 * 3600)

                            if duration is None or duration >= 0:
                                all_found_routes.append(new_path)
                                if len(all_found_routes) >= limit:
                                    queue.clear()
                                    internal_queue.clear()
                                    break
                        
                        # Add to main BFS queue for Transshipment (next leg)
                        if len(new_path) < self.max_legs:
                            visited_ports = {leg['pol_pc'].port_id for leg in new_path}
                            if next_pc.port_id not in visited_ports:
                                queue.append((next_pc.port_id, new_path, current_leg_latest))

                    # Chaining: Check for linked schedules
                    for s_next in next_schedules.get(curr_s.id, []):
                        if s_next.id not in used_schedule_ids and s_next.id not in leg_schedules_ids:
                            if s_next.vessel_id == s.vessel_id:
                                internal_queue.append((s_next, -1, leg_schedules_ids + [s_next.id]))
        
        # 3. Serialization and Sorting
        unique_schedule_ids = set()
        for route in all_found_routes:
            for leg in route:
                for s_id in leg['schedule_ids']:
                    unique_schedule_ids.add(s_id)
        
        from ..serializers import VesselScheduleSerializer
        serialized_schedules = {}
        for s_id in unique_schedule_ids:
            s_obj = schedule_map[s_id]
            serialized_schedules[s_id] = VesselScheduleSerializer(s_obj).data

        final_routes = []
        for path in all_found_routes:
            formatted = self._format_route_v3(path, serialized_schedules)
            final_routes.append(formatted)

        final_routes.sort(key=lambda r: (
            r['legs_count'],
            r['total_duration_days'] if r['total_duration_days'] is not None else 999
        ))

        return final_routes

    def _format_route_v3(self, path, serialized_schedules):
        legs_data = []
        vessel_display_names = []
        
        for leg_idx, leg in enumerate(path):
            leg_vessel_name = None
            for s_idx, s_id in enumerate(leg['schedule_ids']):
                # Create a specific copy for this route leg to allow custom annotation
                s_data = dict(serialized_schedules[s_id])
                
                # Mark the entry and exit port calls for this route segment
                # If it's the first voyage in the chain, it has the loading port
                s_data['route_loading_pc_id'] = leg['pol_pc'].id if s_idx == 0 else None
                # If it's the last voyage in the chain, it has the discharging port
                s_data['route_discharging_pc_id'] = leg['pod_pc'].id if s_idx == len(leg['schedule_ids']) - 1 else None
                
                legs_data.append(s_data)
                leg_vessel_name = s_data['vessel_name']
            
            # De-duplicate consecutive identical vessel names for the summary view
            if not vessel_display_names or vessel_display_names[-1] != leg_vessel_name:
                vessel_display_names.append(leg_vessel_name)
        
        pol_leg = path[0]
        pod_leg = path[-1]
        
        total_duration = None
        if pol_leg['pol_pc'].etd and pod_leg['pod_pc'].eta:
            total_duration = round((pod_leg['pod_pc'].eta - pol_leg['pol_pc'].etd).total_seconds() / (24 * 3600), 1)
        elif pol_leg['pol_pc'].eta and pod_leg['pod_pc'].eta:
            total_duration = round((pod_leg['pod_pc'].eta - pol_leg['pol_pc'].eta).total_seconds() / (24 * 3600), 1)

        route = {
            'type': 'DIRECT' if len(path) == 1 else 'TRANSSHIPMENT',
            'legs_count': len(path),
            'total_duration_days': total_duration,
            'legs': legs_data,
            'vessel_names': vessel_display_names # Combined list for cleaner UI summary
        }

        if len(path) > 1:
            route['trans_port_name'] = path[0]['pod_pc'].port.name
            route['trans_port_code'] = path[0]['pod_pc'].port.code
        
        return route
