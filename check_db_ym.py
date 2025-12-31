
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_proj.settings')
django.setup()

from capacity_tracking.models import VesselSchedule, PortOfCall

def check_db():
    voyages = VesselSchedule.objects.filter(vessel__name__icontains="YM UNIFORMITY", voyage__in=["078E", "078W"]).order_by('voyage')
    
    for vs in voyages:
        print(f"\n--- {vs.vessel.name} {vs.voyage} (ID: {vs.id}) ---")
        print(f"Arrival Berthed: {vs.arrival_berthed}")
        print(f"Previous Schedule: {vs.previous_schedule}")
        ports = vs.port_of_calls.all().order_by('port_order')
        for pc in ports:
            print(f"  Order: {pc.port_order} | Port: {pc.port.name} ({pc.port.code}) | ETA: {pc.eta} | Status: {pc.status}")

if __name__ == "__main__":
    check_db()
