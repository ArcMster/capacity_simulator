
import os
import sys
import django
import json

# Setup Django environment
sys.path.append('/home/sreenath/My projects/Cap/capacity_proj')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_proj.settings')
django.setup()

from capacity_tracking.utils.schedule_parser import parse_schedule_image

# Use the ASX schedule image (uploaded_image_0...)
image_path = '/home/sreenath/.gemini/antigravity/brain/e2042dfd-7e49-42f7-a927-75c5acc533cd/uploaded_image_1_1764615783547.png'

print(f"Testing parser with image: {image_path}")

try:
    schedules = parse_schedule_image(image_path, debug_mode=True)
    # Filter for ZHONG GU NAN NING and voyage 25049
    target_schedules = [
        s for s in schedules 
        if s['v'] == 'ZHONG GU NAN NING' and '25049' in s['voy']
    ]
    print(json.dumps(target_schedules, indent=2))
except Exception as e:
    print(f"Error: {e}")
