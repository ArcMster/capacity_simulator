
import google.generativeai as genai
import os
import sys
from django.conf import settings

# Setup Django minimal
sys.path.append('/home/sreenath/My projects/Cap/capacity_proj')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_proj.settings')
import django
django.setup()

genai.configure(api_key=settings.GOOGLE_API_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
