import os
import django
from django.conf import settings
from django.test import RequestFactory
import json

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
        ROOT_URLCONF='capacity_proj.urls',
    )
    django.setup()

from capacity_tracking.views import autocomplete_port, autocomplete_vessel_schedule

factory = RequestFactory()

print("--- Testing Port Autocomplete ---")
# Create a request for "Jebel"
request = factory.get('/api/autocomplete/port/?q=Jebel')
response = autocomplete_port(request)
print(f"Status Code: {response.status_code}")
print(f"Content: {response.content.decode('utf-8')}")

print("\n--- Testing Vessel Autocomplete ---")
# Create a request for a vessel name (assuming one exists, e.g., "CELSIUS")
request = factory.get('/api/autocomplete/vessel/?q=CELSIUS')
response = autocomplete_vessel_schedule(request)
print(f"Status Code: {response.status_code}")
print(f"Content: {response.content.decode('utf-8')}")
