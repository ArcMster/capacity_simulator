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

from capacity_tracking.models import SlotOpening, VesselSchedule

print("--- Listing All Slot Openings ---")
openings = SlotOpening.objects.all()
for op in openings:
    print(f"SlotOpening ID: {op.id}")
    print(f"  Vessel Schedule: {op.vessel_schedule.id} - {op.vessel_schedule.voyage}")
    print(f"  To Vessel Schedule: {op.to_vessel_schedule}")

print("\n--- Listing All Schedules ---")
schedules = VesselSchedule.objects.all()
for s in schedules:
    print(f"Schedule ID: {s.id}, Voyage: {s.voyage}, Vessel: {s.vessel.name}")
