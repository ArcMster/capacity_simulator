import os
import django
from django.conf import settings
from django.template import Engine

# Configure Django settings manually for the script
BASE_DIR = '/home/sreenath/My projects/Cap/capacity_proj'
if not settings.configured:
    settings.configure(
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(BASE_DIR, 'capacity_tracking/templates')],
            'APP_DIRS': True,
        }],
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'capacity_tracking',
        ]
    )
    django.setup()

file_path = os.path.join(BASE_DIR, 'capacity_tracking/templates/capacity_tracking/search_schedule.html')

print(f"--- Content of {file_path} around line 409 ---")
with open(file_path, 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 400 <= i + 1 <= 420:
            print(f"{i+1}: {repr(line)}")

print("\n--- Attempting to parse template ---")
try:
    with open(file_path, 'r') as f:
        template_content = f.read()
    engine = Engine.get_default()
    template = engine.from_string(template_content)
    print("Template parsed successfully!")
except Exception as e:
    print(f"Template parsing failed: {e}")
