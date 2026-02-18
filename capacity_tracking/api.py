from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch, F, Q
from .models import (
    VesselSchedule, PortOfCall, SlotOpening, SlotWeightStatus, 
    Vessel, Port, Vendor, SlotContractVesselScheduleMapping, ContractPortPairRate
)
from .serializers import (
    VesselScheduleSerializer, PortSerializer, VesselSerializer, VendorSerializer
)
from .forms import ScheduleUploadForm
from .utils.schedule_parser import parse_schedule_image, process_schedule_data
import os
from django.core.files.storage import FileSystemStorage

class VesselScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VesselScheduleSerializer

    def get_queryset(self):
        queryset = VesselSchedule.objects.select_related('vessel', 'service').prefetch_related(
            Prefetch('port_of_calls', queryset=PortOfCall.objects.select_related('port').order_by('port_order')),
            Prefetch('slotopening_set', queryset=SlotOpening.objects.select_related('operator', 'port', 'to_port', 'to_vessel_schedule__vessel')),
            'slotopening_set__slotweightstatus_set'
        )

        from_port_id = self.request.query_params.get('from_port_id')
        to_port_id = self.request.query_params.get('to_port_id')
        vessel_schedule_id = self.request.query_params.get('vessel_schedule_id')
        operator_id = self.request.query_params.get('operator_id')

        if from_port_id and to_port_id:
            # Route Search: Find schedules that have BOTH ports in the correct order
            # This is complex in ORM, so we filter by both first, then refine in list() 
            # or use window functions/nested queries if performance is critical.
            # Simplified for now: return all that have both, then filter order in memory for small datasets.
            queryset = queryset.filter(
                port_of_calls__port_id=from_port_id
            ).filter(
                port_of_calls__port_id=to_port_id
            )
        elif from_port_id:
            queryset = queryset.filter(port_of_calls__port_id=from_port_id)
        elif to_port_id:
            queryset = queryset.filter(port_of_calls__port_id=to_port_id)

        if vessel_schedule_id:
            queryset = queryset.filter(id=vessel_schedule_id)
        if operator_id:
            queryset = queryset.filter(slotopening__operator_id=operator_id)

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        from_port_id = self.request.query_params.get('from_port_id')
        to_port_id = self.request.query_params.get('to_port_id')

        # Filter by ports if provided (Schedules that visit these ports)
        if from_port_id:
            try:
                queryset = queryset.filter(port_of_calls__port_id=int(from_port_id))
            except ValueError: pass
        if to_port_id:
            try:
                queryset = queryset.filter(port_of_calls__port_id=int(to_port_id))
            except ValueError: pass

        queryset = queryset.distinct()
        
        # Recalculate summary fields (operators, balance) for the schedule list
        schedules = list(queryset)
        for s in schedules:
            # Simple summary logic
            s._total_operators = s.slotopening_set.values('operator').distinct().count()
            
            total_bal = 0
            for opening in s.slotopening_set.all():
                for sws in opening.slotweightstatus_set.all():
                    total_bal += (sws.total_slots or 0) - (sws.provisioned_slots or 0) - (sws.used_slots or 0)
            s._total_balance = total_bal
            s._travel_time_days = None # Not used in simple list

        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def find_routes(self, request):
        from_port_id = request.query_params.get('from_port_id')
        to_port_id = request.query_params.get('to_port_id')
        start_date = request.query_params.get('start_date')

        if not (from_port_id and to_port_id):
            return Response({'error': 'Both from_port_id and to_port_id are required'}, status=400)

        from .services.routing import RouteFinderService
        service = RouteFinderService()
        try:
            routes = service.find_routes(from_port_id, to_port_id, start_date=start_date)
            return Response(routes)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

class AutocompleteViewSet(viewsets.ViewSet):
    def port(self, request):
        query = request.GET.get('q', '')
        ports = Port.objects.filter(Q(name__icontains=query) | Q(code__icontains=query))[:20]
        serializer = PortSerializer(ports, many=True)
        return Response(serializer.data)

    def vessel(self, request):
        query = request.GET.get('q', '')
        schedules = VesselSchedule.objects.select_related('vessel').filter(
            Q(vessel__name__icontains=query) | Q(voyage__icontains=query)
        ).distinct()[:20]
        results = [{'id': s.id, 'label': f"{s.vessel.name} - {s.voyage}", 'value': s.voyage} for s in schedules]
        return Response(results)

    def operator(self, request):
        query = request.GET.get('q', '')
        operators = Vendor.objects.filter(name__icontains=query)[:20]
        serializer = VendorSerializer(operators, many=True)
        return Response(serializer.data)

class UploadScheduleAPIView(views.APIView):
    def post(self, request):
        form = ScheduleUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['schedule_file']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(filename)
            results = []
            try:
                schedules_data_list = parse_schedule_image(file_path)
                for schedule_data in schedules_data_list:
                    result_msg = process_schedule_data(schedule_data)
                    results.append(result_msg)
                return Response({'results': results}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
