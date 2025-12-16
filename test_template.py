import os
import sys
import django
from django.template.loader import render_to_string
from django.conf import settings

# Setup Django standalone
sys.path.append('/home/sreenath/My projects/Cap/capacity_proj')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_proj.settings')
django.setup()

try:
    # Try to render the template
    # We don't need real context, just enough to parse the template
    print("Attempting to render template...")
    rendered = render_to_string('capacity_tracking/search_schedule.html', {'schedules': []})
    print("Template rendered successfully!")
except Exception as e:
    print(f"Template rendering failed: {e}")
