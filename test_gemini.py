import google.generativeai as genai
import os
from django.conf import settings
import sys

# Setup Django standalone to get settings
import django
sys.path.append('/home/sreenath/My projects/Cap/capacity_proj')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_proj.settings')
django.setup()

api_key = getattr(settings, 'GOOGLE_API_KEY', None)
print(f"API Key found: {bool(api_key)}")

if api_key:
    genai.configure(api_key=api_key)
    
    # Create a dummy PDF
    with open('test.pdf', 'wb') as f:
        f.write(b'%PDF-1.4\n%...')
    
    try:
        print("Uploading file...")
        f = genai.upload_file('test.pdf', mime_type='application/pdf')
        print(f"Upload success: {f.name}")
    except Exception as e:
        print(f"Error uploading: {e}")
else:
    print("No API key.")
