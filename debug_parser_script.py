
import os
import sys
import django
import json

# Setup Django
sys.path.append('/home/sreenath/My projects/Cap/capacity_proj')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_proj.settings')
django.setup()

from capacity_tracking.utils.schedule_parser import parse_schedule_image

def debug_parser():
    file_path = '/home/sreenath/My projects/Cap/capacity_proj/debug_test.pdf'
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Testing parser with: {file_path}")
    try:
        schedules = parse_schedule_image(file_path, debug_mode=True)
        print("\n--- Parsed Schedules ---")
        print(json.dumps(schedules, indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_parser()
