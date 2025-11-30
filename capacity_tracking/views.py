from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.db.models import Sum, Prefetch, F, Q
from .models import VesselSchedule, PortOfCall, SlotOpening, SlotWeightStatus, Vessel, Port, Vendor

def schedule_api(request):
    """
    Returns JSON data for the vessel schedule, including port calls and operator slot totals.
    """
    queryset = VesselSchedule.objects.select_related('vessel', 'service').prefetch_related(
        Prefetch('port_of_calls', queryset=PortOfCall.objects.select_related('port').order_by('port_order')),
        Prefetch('slotopening_set', queryset=SlotOpening.objects.select_related('operator', 'vessel_schedule')),
        'slotopening_set__slotweightstatus_set'
    )

    # Filtering
    service_code = request.GET.get('service')
    if service_code:
        queryset = queryset.filter(service__code=service_code)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        queryset = queryset.filter(arrival_berthed__range=[start_date, end_date])

    data = []
    for schedule in queryset:
        # Port Calls
        port_calls_data = []
        for pc in schedule.port_of_calls.all():
            port_calls_data.append({
                'port_code': pc.port.code,
                'port_name': pc.port.name,
                'eta': pc.eta,
                'etd': pc.etd,
                'status': pc.status,
                'port_status': pc.port_status,
                'call_no': pc.call_no
            })

        # Operator Slots Aggregation
        operator_slots = {}
        for opening in schedule.slotopening_set.all():
            operator_name = opening.operator.name if opening.operator else "Unknown"
            total = 0
            for status in opening.slotweightstatus_set.all():
                total += status.total_slots
            
            if operator_name in operator_slots:
                operator_slots[operator_name] += total
            else:
                operator_slots[operator_name] = total

        data.append({
            'id': schedule.id,
            'vessel_name': schedule.vessel.name,
            'voyage': schedule.voyage,
            'service_code': schedule.service.code,
            'port_calls': port_calls_data,
            'operator_slots': operator_slots
        })

    return JsonResponse(data, safe=False)

class ScheduleDashboardView(TemplateView):
    template_name = 'capacity_tracking/schedule.html'


def autocomplete_port(request):
    query = request.GET.get('q', '')
    ports = Port.objects.filter(
        Q(name__icontains=query) | Q(code__icontains=query)
    )[:20]
    results = [{'id': p.id, 'label': f"{p.name} ({p.code})", 'value': p.name} for p in ports]
    return JsonResponse(results, safe=False)

def autocomplete_vessel_schedule(request):
    query = request.GET.get('q', '')
    # Search by Vessel Name or Voyage
    schedules = VesselSchedule.objects.select_related('vessel').filter(
        Q(vessel__name__icontains=query) | Q(voyage__icontains=query)
    ).distinct()[:20]
    results = [{'id': s.id, 'label': f"{s.vessel.name} - {s.voyage}", 'value': s.voyage} for s in schedules]
    return JsonResponse(results, safe=False)

def autocomplete_operator(request):
    query = request.GET.get('q', '')
    operators = Vendor.objects.filter(name__icontains=query)[:20]
    results = [{'id': o.id, 'label': o.name, 'value': o.name} for o in operators]
    return JsonResponse(results, safe=False)

def search_schedule_view(request):
    # Get Filter Parameters (IDs)
    from_port_id = request.GET.get('from_port_id')
    to_port_id = request.GET.get('to_port_id')
    vessel_schedule_id = request.GET.get('vessel_schedule_id')
    operator_id = request.GET.get('operator_id')

    # Base QuerySet for Schedules
    schedules_qs = VesselSchedule.objects.all()

    if from_port_id:
        schedules_qs = schedules_qs.filter(port_of_calls__port_id=from_port_id)
    
    if to_port_id:
        schedules_qs = schedules_qs.filter(port_of_calls__port_id=to_port_id)

    if vessel_schedule_id:
        schedules_qs = schedules_qs.filter(id=vessel_schedule_id)

    if operator_id:
        schedules_qs = schedules_qs.filter(slotopening__operator_id=operator_id)

    schedules_qs = schedules_qs.distinct().order_by('id')

    # Fetch Data using the user's logic pattern
    vessel_schedules = list(schedules_qs.values('id', 'voyage', 'status', 'service_id').annotate(
        service=F('service__name'), 
        vessel=F('vessel__name'),
        previous_voyage=F('previous_schedule__voyage')
    ))
    
    schedule_ids = [s['id'] for s in vessel_schedules]

    port_of_calls = list(PortOfCall.objects.filter(vessel_schedule_id__in=schedule_ids).values(
        'id','eta', 'etd','ata', 'atd', 'status', 'port_status', 'call_no','vessel_schedule_id', 'port_id'
    ).annotate(port_code=F('port__code'), port_name=F('port__name'), to_port_code=F('to_port__code')).order_by('port_order'))

    # Filter Slot Openings based on search criteria
    slot_openings_qs = SlotOpening.objects.filter(vessel_schedule_id__in=schedule_ids)
    
    if from_port_id:
        slot_openings_qs = slot_openings_qs.filter(port_id=from_port_id)
    
    if to_port_id:
        slot_openings_qs = slot_openings_qs.filter(to_port_id=to_port_id)

    if operator_id:
        slot_openings_qs = slot_openings_qs.filter(operator_id=operator_id)

    slot_openings = list(slot_openings_qs.values(
        'id', 'opening_criteria', 'vessel_schedule_id', 'call_port_id', 'to_vessel_schedule_id').annotate(
            port_of_call_id=F('call_port_id'),
            to_call_port_id=F('to_call_port_id'),
            operator_id=F('operator_id'),
            operator_name=F('operator__name'),
            port_pair_from=F('port__code'),
            port_pair_to=F('to_port__code'),
            to_vessel_name=F('to_vessel_schedule__vessel__name'),
            to_voyage=F('to_vessel_schedule__voyage')
            ).order_by('call_port__port_order'))
            
    slot_opening_ids = [so['id'] for so in slot_openings]
    
    slot_weight_status = list(SlotWeightStatus.objects.filter(slot_opening_id__in=slot_opening_ids).values(
        'id', 'total_slots', 'used_slots', 'provisioned_slots', 'slot_opening_id',
        'total_weight', 'used_weight', 'provisioned_weight', 'status'))

    # Mapping for Opening Criteria Display
    criteria_map = dict(SlotOpening.OPENING_CRITERIA)
    
    # Mapping for Status Display
    status_map = {
        'LADN': 'Laden',
        'TRST': 'Transshipment',
        'EMTY': 'Empty'
    }

    # Fetch Contract Data
    from .models import SlotContract, SlotContractVesselScheduleMapping, ContractPortPairRate

    # 1. Get Contracts mapped to these schedules
    contract_mappings = list(SlotContractVesselScheduleMapping.objects.filter(
        vessel_schedule_id__in=schedule_ids
    ).values('vessel_schedule_id', 'slot_contract_id', 'slot_contract__operator_id', 
             'slot_contract__contract_criteria', 'slot_contract__slot_rate'))

    # Map: (vessel_schedule_id, operator_id) -> Contract Data
    # Assuming one contract per operator per schedule for simplicity as per current requirements
    schedule_operator_contract_map = {}
    contract_ids = set()
    for mapping in contract_mappings:
        key = (mapping['vessel_schedule_id'], mapping['slot_contract__operator_id'])
        schedule_operator_contract_map[key] = mapping
        contract_ids.add(mapping['slot_contract_id'])

    # 2. Get Port Pair Rates for these contracts
    pp_rates = list(ContractPortPairRate.objects.filter(
        contract_id__in=contract_ids
    ).values('contract_id', 'port_id', 'to_port_id', 'rate'))

    # Map: (contract_id, from_port_id, to_port_id) -> Rate
    contract_pp_rate_map = {}
    for r in pp_rates:
        contract_pp_rate_map[(r['contract_id'], r['port_id'], r['to_port_id'])] = r['rate']

    out_data_list = []
    for schedule in vessel_schedules:
        # Attach Port Calls
        schedule_port_calls = [pc for pc in port_of_calls if pc['vessel_schedule_id'] == schedule['id']]
        
        # Attach Slot Openings
        schedule_slot_openings = [opening for opening in slot_openings if opening['vessel_schedule_id'] == schedule['id']]
        
        # Check for previous voyage
        if schedule.get('previous_voyage'):
             schedule['previous_voyage_display'] = schedule['previous_voyage']

        for opening in schedule_slot_openings:
            # Check for arrival voyage
            if opening.get('to_vessel_schedule_id'):
                if opening['to_vessel_schedule_id'] != schedule['id']:
                     opening['arrival_voyage'] = f"{opening['to_vessel_name']} - {opening['to_voyage']}"
                else:
                     opening['arrival_voyage'] = schedule['voyage']

            opening['criteria_display'] = criteria_map.get(opening['opening_criteria'], opening['opening_criteria'])
            
            # --- Rate Calculation Logic ---
            opening['rate'] = 'N/A' # Default
            
            # Find contract for this schedule and operator
            contract_info = schedule_operator_contract_map.get((schedule['id'], opening['operator_id']))
            
            if contract_info:
                criteria = contract_info['slot_contract__contract_criteria']
                contract_id = contract_info['slot_contract_id']
                from_pid = opening['call_port_id']
                to_pid = opening['to_call_port_id'] # Note: slot_openings query needs to ensure this is available
                
                # Logic 1: Segment Contract or Segment Direct
                if criteria in ['SEGM', 'SEGMDIR']:
                    rate = contract_pp_rate_map.get((contract_id, from_pid, to_pid))
                    if rate is None:
                         # Try generic rate (to_port=None)
                         rate = contract_pp_rate_map.get((contract_id, from_pid, None))
                    
                    if rate is not None:
                        opening['rate'] = rate
                    else:
                        # Fallback to slot_rate
                        opening['rate'] = contract_info['slot_contract__slot_rate']
                
                # Logic 2: Dead Freight
                elif criteria == 'DEAD':
                    # Always try to get rate from ContractPortPairRate first
                    # 1. Try direct rate
                    direct_rate = contract_pp_rate_map.get((contract_id, from_pid, to_pid))
                    if direct_rate is not None:
                        opening['rate'] = direct_rate
                    else:
                        # 2. Calculate sum of available port-pairs
                        # Check if to_pid is in the current schedule
                        schedule_port_ids = [pc['port_id'] for pc in schedule_port_calls]
                        
                        search_end_pid = None
                        additional_rate = 0
                        valid_setup = False

                        if to_pid in schedule_port_ids:
                            search_end_pid = to_pid
                            valid_setup = True
                        elif opening.get('to_vessel_schedule_id') and opening['to_vessel_schedule_id'] != schedule['id']:
                            # Multi-voyage: Path to last port, then add last_port -> to_pid
                            if schedule_port_calls:
                                last_port = schedule_port_calls[-1]
                                search_end_pid = last_port['port_id']
                                
                                # Try to get the connecting rate (Last Port -> Discharge)
                                connecting_rate = contract_pp_rate_map.get((contract_id, search_end_pid, to_pid))
                                if connecting_rate is not None:
                                    additional_rate = connecting_rate
                                    valid_setup = True
                        
                        if valid_setup and search_end_pid:
                            # Find indices of from and to ports in the current schedule
                            try:
                                start_idx = next(i for i, pc in enumerate(schedule_port_calls) if pc['port_id'] == from_pid)
                                end_idx = next(i for i, pc in enumerate(schedule_port_calls) if pc['port_id'] == search_end_pid)
                                
                                if start_idx <= end_idx: # Allow start == end if that's the only segment needed (though unlikely for sum)
                                    path_ports = schedule_port_calls[start_idx : end_idx + 1]
                                    total_rate = 0
                                    found_path = True
                                    
                                    # If start == end (e.g. Load is Last Port), loop won't run, total_rate = 0. 
                                    # Logic should handle this if we just need additional_rate.
                                    
                                    curr_idx = 0
                                    while curr_idx < len(path_ports) - 1:
                                        p1 = path_ports[curr_idx]['port_id']
                                        segment_found = False
                                        for next_offset in range(1, len(path_ports) - curr_idx):
                                            p2 = path_ports[curr_idx + next_offset]['port_id']
                                            r = contract_pp_rate_map.get((contract_id, p1, p2))
                                            if r is not None:
                                                total_rate += r
                                                curr_idx += next_offset
                                                segment_found = True
                                                break
                                        
                                        if not segment_found:
                                            found_path = False
                                            break
                                    
                                    if found_path:
                                        opening['rate'] = total_rate + additional_rate
                                    else:
                                        opening['rate'] = 'N/A'
                                else:
                                    # Start is after End (shouldn't happen in valid schedule flow)
                                    opening['rate'] = 'N/A'

                            except StopIteration:
                                # Ports not found
                                pass
                        
                        # Fallback: If calculation failed (N/A), use the base slot_rate
                        if opening['rate'] == 'N/A':
                             opening['rate'] = contract_info['slot_contract__slot_rate']

            opening['statuses'] = []
            for status in slot_weight_status:
                if status['slot_opening_id'] == opening['id']:
                    # Create a copy or modify in place (safe here as we build fresh list)
                    s_copy = status.copy()
                    s_copy['status'] = status_map.get(status['status'], status['status'])
                    # Calculate balance for the template
                    total = s_copy.get('total_slots') or 0
                    used = s_copy.get('used_slots') or 0
                    provisioned = s_copy.get('provisioned_slots') or 0
                    
                    s_copy['blocked'] = provisioned + used
                    s_copy['balance'] = total - provisioned - used
                    opening['statuses'].append(s_copy)
        
        # Calculate Aggregates for the Dashboard View
        unique_operators = set(op['operator_id'] for op in schedule_slot_openings)
        schedule['total_operators'] = len(unique_operators)
        
        total_balance = 0
        for opening in schedule_slot_openings:
            for status in opening['statuses']:
                # Ensure we handle None values safely, though model defaults should prevent this
                total = status.get('total_slots') or 0
                used = status.get('used_slots') or 0
                provisioned = status.get('provisioned_slots') or 0
                total_balance += (total - provisioned - used)
        
        schedule['total_balance'] = total_balance

        schedule['port_calls'] = schedule_port_calls
        schedule['slot_openings'] = schedule_slot_openings
        out_data_list.append(schedule)

    # Calculate Summary Metrics
    total_schedules = len(out_data_list)
    total_balance_slots = sum(s['total_balance'] for s in out_data_list)
    
    # Get unique operators across all found schedules
    all_operator_ids = set()
    for s in out_data_list:
        for opening in s['slot_openings']:
            all_operator_ids.add(opening['operator_id'])
    unique_operators_count = len(all_operator_ids)

    context = {
        'schedules': out_data_list,
        'summary': {
            'total_schedules': total_schedules,
            'total_balance_slots': total_balance_slots,
            'unique_operators_count': unique_operators_count
        }
    }

    return render(request, 'capacity_tracking/search_schedule.html', context)