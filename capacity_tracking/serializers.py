from rest_framework import serializers
from .models import (
    Vessel, Service, Port, Terminal, Vendor, VesselSchedule, 
    PortOfCall, SlotOpening, SlotWeightStatus, SlotContract, 
    SlotContractVesselScheduleMapping, ContractPortPairRate
)

class VesselSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vessel
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = '__all__'

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'

class PortOfCallSerializer(serializers.ModelSerializer):
    port_name = serializers.ReadOnlyField(source='port.name')
    port_code = serializers.ReadOnlyField(source='port.code')
    to_port_code = serializers.ReadOnlyField(source='to_port.code')
    
    class Meta:
        model = PortOfCall
        fields = '__all__'

class SlotWeightStatusSerializer(serializers.ModelSerializer):
    blocked = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    status_display = serializers.ReadOnlyField(source='get_status_display')

    class Meta:
        model = SlotWeightStatus
        fields = '__all__'

    def get_blocked(self, obj):
        return (obj.provisioned_slots or 0) + (obj.used_slots or 0)

    def get_balance(self, obj):
        return (obj.total_slots or 0) - self.get_blocked(obj)

class SlotOpeningSerializer(serializers.ModelSerializer):
    operator_name = serializers.ReadOnlyField(source='operator.name')
    port_pair_from = serializers.ReadOnlyField(source='port.code')
    port_pair_to = serializers.ReadOnlyField(source='to_port.code')
    criteria_display = serializers.ReadOnlyField(source='get_opening_criteria_display')
    statuses = SlotWeightStatusSerializer(source='slotweightstatus_set', many=True, read_only=True)
    rate = serializers.SerializerMethodField()
    arrival_voyage = serializers.SerializerMethodField()
    dest_eta = serializers.SerializerMethodField()

    class Meta:
        model = SlotOpening
        fields = '__all__'

    def get_rate(self, obj):
        # This logic is complex and was originally in views.py.
        # For now, I'll return 'N/A' and implement the full logic if needed, 
        # or rely on the frontend to display if we pass the components.
        # Actually, let's keep the backend logic for consistency.
        return getattr(obj, '_computed_rate', 'N/A')

    def get_arrival_voyage(self, obj):
        if obj.to_vessel_schedule:
            if obj.to_vessel_schedule_id != obj.vessel_schedule_id:
                return f"{obj.to_vessel_schedule.vessel.name} - {obj.to_vessel_schedule.voyage}"
            return obj.vessel_schedule.voyage
        return None

    def get_dest_eta(self, obj):
        return getattr(obj, '_dest_eta', None)

class VesselScheduleSerializer(serializers.ModelSerializer):
    vessel_name = serializers.ReadOnlyField(source='vessel.name')
    service_code = serializers.ReadOnlyField(source='service.code')
    vessel = VesselSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    port_calls = PortOfCallSerializer(source='port_of_calls', many=True, read_only=True)
    total_operators = serializers.SerializerMethodField()
    total_balance = serializers.SerializerMethodField()
    travel_time_days = serializers.SerializerMethodField()

    class Meta:
        model = VesselSchedule
        fields = [
            'id', 'vessel_name', 'service_code', 'port_calls',
            'total_operators', 'total_balance', 'travel_time_days',
            'voyage', 'status', 'arrival_berthed', 'departure_time',
            'is_phase_in', 'direction', 'vessel', 'service', 'previous_schedule'
        ]

    def get_total_operators(self, obj):
        return getattr(obj, '_total_operators', 0)

    def get_total_balance(self, obj):
        return getattr(obj, '_total_balance', 0)

    def get_travel_time_days(self, obj):
        return getattr(obj, '_travel_time_days', None)
