
import google.generativeai as genai
import json
import os
import logging
from datetime import datetime
from django.conf import settings
from django.utils.timezone import make_aware
import dateutil.parser
from capacity_tracking.models import Vessel, Service, Port, VesselSchedule, PortOfCall

# Configure Logger
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.GOOGLE_API_KEY)

def parse_schedule_image(image_path, debug_mode=False):
    """
    Parses a vessel schedule image/PDF using Google Gemini API.
    Returns a list of structured schedule dictionaries.
    """
    
    prompt = """
    Analyze this vessel schedule document. 
    Identify the table that contains vessel schedules.
    Extract the following information for EACH vessel voyage found:
    
    1. Vessel Name
    2. Voyage Number
    3. Service Code (if mentioned, otherwise null)
    4. Service Name (if mentioned, otherwise null)
    5. List of Port Calls. For each port call, extract:
       - Port Name
       - Arrival Date (ETA) - Format as String
       - Departure Date (ETD) - Format as String
       - Status (if valid status like OMIT/SKIP is found, otherwise null)

    Return the output as a JSON object with a key "schedules" containing a list of objects.
    
    JSON Structure:
    {
      "schedules": [
        {
          "vessel_name": "VALUE",
          "voyage_number": "VALUE",
          "service_code": "VALUE", 
          "port_calls": [
            {
              "port_name": "VALUE",
              "eta": "VALUE", 
              "etd": "VALUE",
              "status": "VALUE"
            }, 
            ...
          ]
        },
        ...
      ]
    }
    
    Notes:
    - If a date is just a day/month (e.g. "05-Dec"), assume the current or next plausible year.
    - If "OMIT" or similar is found in dates, mark status as "OMITTED".
    """

    model_name = 'gemini-flash-latest'

    model = genai.GenerativeModel(model_name)
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")
        
    mime_type = "application/pdf"
    if image_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        if image_path.lower().endswith('.png'):
            mime_type = "image/png"
        else:
            mime_type = "image/jpeg"
            
    # Upload file (Gemini File API is recommended for complex PDFs, but for now we try passing data directly if small, 
    # but 2.0 Flash supports PDF input via parts)
    # For simplicity in this environment, we will read bytes.
    
    with open(image_path, "rb") as f:
        file_data = f.read()
        
    content_parts = [
        prompt,
        {
            "mime_type": mime_type,
            "data": file_data
        }
    ]
    
    generation_config = {
        "temperature": 0.1,
        "response_mime_type": "application/json",
    }

    response = model.generate_content(content_parts, generation_config=generation_config)
    
    # Debug: Log raw response
    try:
        with open('last_gemini_response.txt', 'w') as f:
            f.write(response.text)
    except:
        pass
    
    # Parse JSON
    text = response.text.strip()
    # Clean potential markdown code blocks
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
        
    data = json.loads(text)
    return data.get("schedules", [])

def process_schedule_data(schedule_data):
    """
    Takes a single schedule dictionary (from parse_schedule_image) and persists it to Django models.
    Returns a success message or error string.
    """
    try:
        vessel_name = schedule_data.get("vessel_name")
        voyage_number = schedule_data.get("voyage_number")
        service_code = schedule_data.get("service_code") or "GEN"
        port_calls = schedule_data.get("port_calls", [])

        if not vessel_name or not voyage_number:
            return "Skipped: Missing Vessel Name or Voyage Number."

        # 1. Handle Vessel
        # Normalize name
        vessel_name = vessel_name.strip().upper()
        vessel, _ = Vessel.objects.get_or_create(
            name=vessel_name,
            defaults={"code": vessel_name[:10]} # Simple default code
        )

        # 2. Handle Service
        service, _ = Service.objects.get_or_create(
            code=service_code,
            defaults={"name": schedule_data.get("service_name") or service_code}
        )

        # 3. Handle VesselSchedule
        # valid status: UCMP (Uncompleted), CMPL (Completed)
        schedule, created = VesselSchedule.objects.update_or_create(
            vessel=vessel,
            voyage=voyage_number,
            defaults={
                "service": service,
                "status": "UCMP"
            }
        )

        # 4. Handle Port Calls
        # Overwrite existing calls to ensure sync
        schedule.port_of_calls.all().delete()

        created_count = 0
        first_eta = None
        last_etd = None

        for idx, call in enumerate(port_calls):
            p_name = call.get("port_name")
            if not p_name: 
                continue
                
            p_name = p_name.strip()
            
            # Find Port
            # Try exact match first
            port = Port.objects.filter(name__iexact=p_name).first()
            if not port:
                # Try code match if name looks like a code (3-5 uppercase chars)
                if len(p_name) <= 5 and p_name.isupper():
                    port = Port.objects.filter(code=p_name).first()
            
            if not port:
                # Create Port
                # Generate a code: First 5 letters of name, upper
                new_code = p_name.replace(" ", "")[:5].upper()
                # Ensure uniqueness
                counter = 1
                final_code = new_code
                while Port.objects.filter(code=final_code).exists():
                    final_code = f"{new_code[:3]}{counter:02d}"
                    counter += 1
                
                port = Port.objects.create(name=p_name, code=final_code)

            # Parse Dates
            eta = parse_dt(call.get("eta"))
            etd = parse_dt(call.get("etd"))

            if idx == 0:
                first_eta = eta
            
            last_etd = etd or last_etd # Keep the last non-null etd
            
            # Status
            status = "NOT ARRIVED"
            raw_status = str(call.get("status", "")).upper()
            if "OMIT" in raw_status:
                status = "OMITTED"
            elif "SAIL" in raw_status:
                status = "SAILED"
            
            PortOfCall.objects.create(
                vessel_schedule=schedule,
                port=port,
                eta=eta,
                etd=etd,
                status=status,
                call_no=str(idx + 1),
                port_order=idx + 1
            )
            created_count += 1

        # 5. Update Schedule Times and Link Previous Schedule
        schedule.arrival_berthed = first_eta
        schedule.departure_time = last_etd
        
        if first_eta:
            # Find the previous schedule: same vessel, latest arrival_berthed < current arrival_berthed
            prev_schedule = VesselSchedule.objects.filter(
                vessel=vessel,
                arrival_berthed__lt=first_eta
            ).order_by('-arrival_berthed').first()
            
            if prev_schedule:
                schedule.previous_schedule = prev_schedule
        
        schedule.save()

        action = "Created" if created else "Updated"
        return f"{action} schedule for {vessel.name} - {voyage_number} with {created_count} ports."

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error processing {schedule_data.get('vessel_name', 'Unknown')}: {str(e)}"

def parse_dt(date_str):
    """
    Helper to parse date strings using dateutil.
    Assumes current year if missing.
    """
    if not date_str:
        return None
    try:
        # cleanup
        date_str = date_str.strip()
        if not date_str or date_str.lower() == "none":
            return None
            
        dt = dateutil.parser.parse(date_str, fuzzy=True)
        
        # Fix year if it defaulted to 1900
        now = datetime.now()
        if dt.year == 1900:
            dt = dt.replace(year=now.year)
            
        return make_aware(dt)
    except:
        return None
