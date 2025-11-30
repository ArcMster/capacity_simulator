from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Vessel)
admin.site.register(Service)
admin.site.register(Port)
admin.site.register(Vendor)
admin.site.register(VesselSchedule)
admin.site.register(PortOfCall)
admin.site.register(SlotOpening)
admin.site.register(SlotWeightStatus)
admin.site.register(SlotContract)
admin.site.register(SlotContractVesselScheduleMapping)
admin.site.register(ContractPortPairRate)

