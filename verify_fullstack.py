import os
import django
import json
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_proj.settings')
django.setup()

from django.test import RequestFactory
from capacity_tracking.models import Vessel, Service, Port, VesselSchedule, PortOfCall, SlotOpening, SlotWeightStatus, Vendor
from capacity_tracking.views import schedule_api

def run_verification():
    print("Setting up test data...")
    # Clean up
    VesselSchedule.objects.all().delete()
    Vessel.objects.all().delete()
    Service.objects.all().delete()
    Port.objects.all().delete()
    Vendor.objects.all().delete()

    # Create Objects
    vessel = Vessel.objects.create(name="TEST VESSEL", code="TV01")
    service = Service.objects.create(name="TEST SERVICE", code="TS01")
    
    p1 = Port.objects.create(name="Port A", code="PTA")
    p2 = Port.objects.create(name="Port B", code="PTB")
    
    op1 = Vendor.objects.create(name="Operator 1", code="OP1")
    op2 = Vendor.objects.create(name="Operator 2", code="OP2")

    schedule = VesselSchedule.objects.create(
        vessel=vessel,
        service=service,
        voyage="V001",
        arrival_berthed=datetime.now(),
        departure_time=datetime.now() + timedelta(days=10)
    )

    # Port Calls
    PortOfCall.objects.create(
        vessel_schedule=schedule, port=p1, port_order=1, 
        eta=datetime.now(), etd=datetime.now()+timedelta(days=1),
        status='SAILED', port_status='ACTIVE'
    )
    PortOfCall.objects.create(
        vessel_schedule=schedule, port=p2, port_order=2,
        eta=datetime.now()+timedelta(days=5), etd=datetime.now()+timedelta(days=6),
        status='NOT SAILED', port_status='OMITTED'
    )

    # Slot Openings
    so1 = SlotOpening.objects.create(
        vessel=vessel, vessel_schedule=schedule, operator=op1, port=p1, to_port=p2
    )
    SlotWeightStatus.objects.create(slot_opening=so1, total_slots=100, status='LADN')
    
    so2 = SlotOpening.objects.create(
        vessel=vessel, vessel_schedule=schedule, operator=op2, port=p1, to_port=p2
    )
    SlotWeightStatus.objects.create(slot_opening=so2, total_slots=50, status='LADN')
    SlotWeightStatus.objects.create(slot_opening=so2, total_slots=20, status='EMTY') # Total 70 for OP2

    print("Calling API...")
    factory = RequestFactory()
    request = factory.get('/api/schedule/')
    response = schedule_api(request)
    
    print(f"Response Status: {response.status_code}")
    content = json.loads(response.content)
    print(json.dumps(content, indent=2, default=str))

    # Assertions
    assert len(content) == 1
    item = content[0]
    assert item['vessel_name'] == "TEST VESSEL"
    assert len(item['port_calls']) == 2
    assert item['operator_slots']['Operator 1'] == 100
    assert item['operator_slots']['Operator 2'] == 70
    
    print("\nVERIFICATION SUCCESSFUL!")

if __name__ == "__main__":
    run_verification()
