
import google.generativeai as genai
import json
import os
import logging
from datetime import datetime
from django.conf import settings
from django.utils.timezone import make_aware
import dateutil.parser
from capacity_tracking.models import Vessel, Service, Port, VesselSchedule, PortOfCall, Terminal

# Configure Logger
logger = logging.getLogger(__name__)

# Configure Gemini API
GOOGLE_API_KEY = getattr(settings, 'GOOGLE_API_KEY', None)
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logger.warning("GOOGLE_API_KEY not found in settings. AI parsing will be unavailable.")

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
    2. Voyage Number (e.g. 096W, 096E)
    3. Direction (Extract "EAST", "WEST", or null based on voyage suffix or rotation headers)
    4. Service Code (if mentioned, otherwise null)
    5. Service Name (if mentioned, otherwise null)
    6. List of Port Calls for this specific voyage/rotation. For each port call, extract:
       - Port Name
       - Terminal (e.g. WGQ2, NBCT 1, PSA - usually found directly under Port name)
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
          "direction": "EAST/WEST/FORWARD/BACKWARD/STRAIGHT",
          "service_code": "VALUE",
          "port_calls": [
            {
              "port_name": "VALUE",
              "terminal_name": "VALUE",
              "eta": "VALUE",
              "etd": "VALUE",
              "status": "VALUE"
            }
          ]
        },
        ...
      ]
    }
    
    Notes:
    - VERY IMPORTANT: "East" and "West" rotations must be treated as SEPARATE objects in the "schedules" list.
    - Horizontal Multi-Voyage Layout: A single row often contains multiple voyage labels (e.g., 078W, 079E) separated by date columns.
    - **Circular/Row Transition Rule (Continuous Loop)**: In services like WIN, a vessel moves in a loop where the last port of an Eastbound leg (e.g., `SGSIN` at the end of `078E` in row 1) is the **starting port** of the Westbound leg in the NEXT row (e.g., `078W` in row 2). Even if the Westbound column starts with `Shanghai`, you MUST check the preceding Eastbound voyage's final port. If it matches the start of the service loop (like `SGSIN`), include it as the first port of the new voyage with the exact same date.
    - **Mid-Row Transition Rule**: Within a single horizontal row, the port immediately preceding a new voyage label (e.g., `MYPKG` before `079E` in row 2) MUST be included in BOTH voyages. It is the LAST port of the preceding voyage (`078W`) and MUST be the FIRST port of the following voyage (`079E`).
    - **Voyage Termination Rule**: Ensure a voyage (e.g., `006`) ends at the port immediately preceding the next voyage label (e.g., `007`).
    - **Repeated Voyage Rule**: If the same voyage number is repeated, group all ports into a SINGLE schedule object.
    - Column Mapping: Precisely map each date to the port header above its column.
    - Date Stacking: Extract both lines (Top: ETA, Bottom: ETD) for each port call.
    - Direction: Assign "WEST" for 'W' suffixes and "EAST" for 'E' suffixes.
    - Year Inference: Ensure dates translate to a valid chronological sequence (e.g., Dec 2025 followed by Jan 2026).
    - Status: Mark as "OMITTED" if "OMIT" or "SKIP" is noted.
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
    schedules = data.get("schedules", [])

    if schedules:
        # Sort schedules by vessel name and the ETA of the first port call to ensure 
        # that 'previous_schedule' links work correctly during processing.
        def get_sort_key(s):
            v_name = s.get("vessel_name", "").upper()
            eta = None
            if s.get("port_calls"):
                first_pc = s["port_calls"][0]
                eta_raw = first_pc.get("eta") or first_pc.get("arrival_date")
                eta = parse_dt(eta_raw)
            return (v_name, eta.isoformat() if eta else "9999-12-31")

        schedules.sort(key=get_sort_key)
    return schedules

def process_schedule_data(schedule_data):
    """
    Takes a single schedule dictionary (from parse_schedule_image) and persists it to Django models.
    Returns a success message or error string.
    """
    try:
        vessel_name = schedule_data.get("vessel_name")
        voyage_number = schedule_data.get("voyage_number")
        service_code = schedule_data.get("service_code") or "GEN"
        direction = schedule_data.get("direction")
        port_calls = schedule_data.get("port_calls", [])

        if not vessel_name or not voyage_number:
            return "Skipped: Missing Vessel Name or Voyage Number."

        if direction:
            direction = direction.strip().upper()
            if direction not in [d[0] for d in VesselSchedule.VOYAGE_DIRECTION]:
                # Attempt mapping for common abbreviations
                if direction == "E": direction = "EAST"
                elif direction == "W": direction = "WEST"
                else: direction = None
        
        # fallback to voyage suffix if direction not explicitly provided
        if not direction and voyage_number:
            if voyage_number.upper().endswith("W"): direction = "WEST"
            elif voyage_number.upper().endswith("E"): direction = "EAST"

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
                "status": "UCMP",
                "direction": direction
            }
        )

        # 4. Handle Port Calls
        port_calls_raw = schedule_data.get("port_calls", [])
        
        # Simple deduplication: remove consecutive identical port+eta entries
        port_calls = []
        for call in port_calls_raw:
            if not port_calls:
                port_calls.append(call)
            else:
                last = port_calls[-1]
                if last.get("port_name") == call.get("port_name") and \
                   (last.get("eta") or last.get("arrival_date")) == (call.get("eta") or call.get("arrival_date")):
                    continue
                port_calls.append(call)
        
        # Get existing port calls to update incrementally
        existing_calls = {pc.port_order: pc for pc in schedule.port_of_calls.all()}
        
        created_count = 0
        updated_count = 0
        first_eta = None
        last_etd = None
        seen_port_orders = []

        for idx, call in enumerate(port_calls):
            p_order = idx + 1
            seen_port_orders.append(p_order)
            
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
            
            # Find/Create Terminal
            t_name = call.get("terminal_name") or "TBN"
            t_name = t_name.strip()
            
            # Use name as code if it's short, otherwise generate
            t_code = t_name.replace(" ", "")[:10].upper()
            if not t_code: t_code = "TBN"
            
            terminal = Terminal.objects.filter(code=t_code).first()
            if not terminal:
                # Double check by name and port if code uniqueness is tricky, 
                # but model says code is unique.
                terminal = Terminal.objects.filter(name=t_name, port=port).first()
                
            if not terminal:
                # Ensure code is unique by adding a suffix if it exists for another terminal
                final_t_code = t_code
                counter = 1
                while Terminal.objects.filter(code=final_t_code).exists():
                    final_t_code = f"{t_code[:7]}{counter:03d}"
                    counter += 1
                terminal = Terminal.objects.create(name=t_name, code=final_t_code, port=port)

            # Parse Dates
            eta_raw = call.get("eta") or call.get("arrival_date")
            etd_raw = call.get("etd") or call.get("departure_date")
            
            eta = parse_dt(eta_raw)
            etd = parse_dt(etd_raw)

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

            if p_order in existing_calls:
                # Update existing
                pc = existing_calls[p_order]
                # Update if changed
                changed = False
                if pc.port != port:
                    pc.port = port
                    changed = True
                if pc.terminal != terminal:
                    pc.terminal = terminal
                    changed = True
                if pc.eta != eta:
                    pc.eta = eta
                    changed = True
                if pc.etd != etd:
                    pc.etd = etd
                    changed = True
                if pc.status != status:
                    pc.status = status
                    changed = True
                
                if changed:
                    pc.save()
                    updated_count += 1
            else:
                # Create new
                PortOfCall.objects.create(
                    vessel_schedule=schedule,
                    port=port,
                    terminal=terminal,
                    eta=eta,
                    etd=etd,
                    status=status,
                    call_no=str(p_order),
                    port_order=p_order
                )
                created_count += 1

        # Delete port calls that are no longer in the schedule
        # IMPORTANT: Preserve port_order=0 (handover port) if it was enriched previously
        schedule.port_of_calls.exclude(port_order__in=seen_port_orders).exclude(port_order=0).delete()

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
                
                # Handover Enrichment Logic
                # Prepend the last port of the previous schedule if it's missing from current
                last_pc_prev = prev_schedule.port_of_calls.order_by('port_order').last()
                first_pc_curr = schedule.port_of_calls.order_by('port_order').first()
                
                if last_pc_prev and first_pc_curr and last_pc_prev.port != first_pc_curr.port:
                    # Robust chronology check for handover
                    # We allow 'None' (Omitted) ports to be correctly prepended as handovers.
                    # Only block if both dates exist and the previous is clearly LATER (which would be invalid).
                    is_invalid_handover = False
                    if last_pc_prev.eta and first_pc_curr.eta and last_pc_prev.eta > first_pc_curr.eta:
                        is_invalid_handover = True
                    
                    if not is_invalid_handover:
                        # Check if port_order 0 already exists (prevents duplicate enrichments)
                        existing_handover = schedule.port_of_calls.filter(port_order=0).first()
                        if not existing_handover:
                            PortOfCall.objects.create(
                                vessel_schedule=schedule,
                                port=last_pc_prev.port,
                                terminal=last_pc_prev.terminal,
                                eta=last_pc_prev.eta,
                                etd=last_pc_prev.etd,
                                status=last_pc_prev.status,
                                call_no="0",
                                port_order=0
                            )
                            # Re-calculate first_eta if we just prepended a port
                            if last_pc_prev.eta:
                                schedule.arrival_berthed = last_pc_prev.eta
                        else:
                            # Update existing handover if it changed
                            changed = False
                            if existing_handover.port != last_pc_prev.port:
                                existing_handover.port = last_pc_prev.port
                                changed = True
                            if existing_handover.eta != last_pc_prev.eta:
                                existing_handover.eta = last_pc_prev.eta
                                changed = True
                            if changed:
                                existing_handover.save()
                                if last_pc_prev.eta:
                                    schedule.arrival_berthed = last_pc_prev.eta
        
        schedule.save()

        action = "Created" if created else "Updated"
        return f"{action} schedule for {vessel.name} - {voyage_number} with {created_count} ports created and {updated_count} ports updated."

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
        date_str = str(date_str).strip()
        if not date_str or date_str.lower() == "none" or "omit" in date_str.lower():
            return None
            
        logger.debug(f"Attempting to parse date: '{date_str}'")
        dt = dateutil.parser.parse(date_str, fuzzy=True)
        
        # Fix year if it defaulted to 1900 or if it's very far in the past
        now = datetime.now()
        if dt.year < 2000:
            dt = dt.replace(year=now.year)
            
        res = make_aware(dt)
        logger.debug(f"Successfully parsed '{date_str}' to {res}")
        return res
    except Exception as e:
        logger.error(f"Failed to parse date string '{date_str}': {str(e)}")
        return None
