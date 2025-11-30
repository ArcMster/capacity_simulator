import os
import django
from django.conf import settings

# Configure Django settings manually for the script
BASE_DIR = '/home/sreenath/My projects/Cap/capacity_proj'
if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'capacity_tracking',
        ],
    )
    django.setup()

from capacity_tracking.models import VesselSchedule, SlotOpening, Port, Vendor, PortOfCall, SlotWeightStatus

print("--- Creating Test Data ---")

try:
    s1 = VesselSchedule.objects.get(id=1) # CFV1000012
    s2 = VesselSchedule.objects.get(id=2) # CFV1000013

    # Ensure Ports exist
    port_from, _ = Port.objects.get_or_create(code='OMSOH', defaults={'name': 'Sohar'})
    port_to, _ = Port.objects.get_or_create(code='AEJEA', defaults={'name': 'Jebel Ali'})
    
    # Ensure Operator exists
    operator, _ = Vendor.objects.get_or_create(code='XPRESS', defaults={'name': 'Xpress Feeders'})

    # Ensure PortOfCall exists for s1
    poc_from, _ = PortOfCall.objects.get_or_create(
        vessel_schedule=s1, 
        port=port_from, 
        defaults={'port_order': 1}
    )

    # Create SlotOpening
    op, created = SlotOpening.objects.get_or_create(
        vessel_schedule=s1,
        port=port_from,
        to_port=port_to,
        operator=operator,
        defaults={
            'vessel': s1.vessel,
            'call_port': poc_from,
            'opening_criteria': 'SEGMDIR'
        }
    )
    
    if created:
        print(f"Created new SlotOpening {op.id}")
    else:
        print(f"Found existing SlotOpening {op.id}")

    # Link to s2
    op.to_vessel_schedule = s2
    op.save()
    print(f"Linked SlotOpening {op.id} to {s2.voyage}")

    # Create SlotWeightStatus
    sws, sws_created = SlotWeightStatus.objects.get_or_create(
        slot_opening=op,
        status='LADN',
        defaults={
            'total_slots': 50,
            'used_slots': 0
        }
    )
    if sws_created:
        print("Created SlotWeightStatus with 50 slots")
    else:
        print("Found existing SlotWeightStatus")

except Exception as e:
    print(f"Error: {e}")
