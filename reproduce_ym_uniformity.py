
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_proj.settings')
django.setup()

from capacity_tracking.utils.schedule_parser import parse_schedule_image, process_schedule_data
from capacity_tracking.models import PortOfCall, VesselSchedule

def test_ym_uniformity():
    file_path = "/home/sreenath/My projects/Cap/capacity_proj/West India North Asia Service (WIN).pdf"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    print(f"--- Parsing {file_path} ---")
    schedules_data = parse_schedule_image(file_path)
    
    if not schedules_data:
        print("No schedules found.")
        return

    # Filter for YM UNIFORMITY
    ym_schedules = [s for s in schedules_data if "YM UNIFORMITY" in s.get("vessel_name", "").upper()]
    
    print(f"Found {len(ym_schedules)} schedules for YM UNIFORMITY.")

    # Process all to ensure enrichment works
    for schedule_data in ym_schedules:
        v_name = schedule_data.get("vessel_name", "")
        v_num = schedule_data.get("voyage_number", "")
        print(f"\n--- Processing {v_name} {v_num} ---")
        # print(json.dumps(schedule_data, indent=2))
        
        result = process_schedule_data(schedule_data)
        print(result)

    # Verify 078E and 078W
    for voyage in ["078E", "078W"]:
        vs = VesselSchedule.objects.filter(vessel__name__icontains="YM UNIFORMITY", voyage=voyage).first()
        if vs:
            print(f"\n--- Ports for {vs.vessel.name} {vs.voyage} ---")
            for pc in vs.port_of_calls.all().order_by('port_order'):
                print(f"Order: {pc.port_order} | Port: {pc.port.name} | ETA: {pc.eta} | Status: {pc.status}")
        else:
            print(f"YM UNIFORMITY {voyage} not found in DB.")

if __name__ == "__main__":
    test_ym_uniformity()
