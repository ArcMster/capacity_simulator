
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_proj.settings')
django.setup()

from capacity_tracking.utils.schedule_parser import parse_schedule_image, process_schedule_data
from capacity_tracking.models import PortOfCall, VesselSchedule

def test_parsing():
    file_path = "/home/sreenath/Downloads/West India North Asia Service (WIN).pdf"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    print(f"--- Parsing {file_path} ---")
    schedules_data = parse_schedule_image(file_path)
    
    if not schedules_data:
        print("No schedules found.")
        return

    # Process all to ensure enrichment works
    for schedule_data in schedules_data:
        v_name = schedule_data.get("vessel_name", "")
        v_num = schedule_data.get("voyage_number", "")
        if "ONE MAGNIFICENCE" in v_name.upper():
            print(f"\n--- Raw JSON for {v_name} {v_num} ---")
            print(json.dumps(schedule_data, indent=2))
        
        process_schedule_data(schedule_data)

    # Verify 079W and 080E
    for voyage in ["079W", "080E"]:
        vs = VesselSchedule.objects.filter(vessel__name__icontains="ONE MAGNIFICENCE", voyage=voyage).first()
        if vs:
            print(f"\n--- Ports for {vs.vessel.name} {vs.voyage} ---")
            for pc in vs.port_of_calls.all().order_by('port_order'):
                print(f"Order: {pc.port_order} | Port: {pc.port.name} | ETA: {pc.eta} | Status: {pc.status}")
        else:
            print(f"ONE MAGNIFICENCE {voyage} not found in DB.")

if __name__ == "__main__":
    test_parsing()
