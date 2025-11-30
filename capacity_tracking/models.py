from django.db import models

# Create your models here.

class Vessel(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Service(models.Model):
    """
    @see https://dcsa.org/
        Information Model v3.3_final
        Service entry.
    """
    code = models.CharField(max_length=25, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Port(models.Model):
    """
    This model is used for defining sea ports and dry ports.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=25, unique=True)

    def __str__(self):
        return self.name

class Vendor(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=25, unique=True)

    def __str__(self):
        return self.name


class VesselSchedule(models.Model):
    """
    For more reference,
    @see https://dcsa.org/
    Operational-Vessel-Schedule-definitions-1.0-vF.pdf
    """
    STATUS = (('UCMP', 'UNCOMPLETED'), ('CMPL', 'COMPLETED'))
    # Note: The status can change in the future

    VOYAGE_DIRECTION = (("FORWARD", "FORWARD"),
                    ("BACKWARD", "BACKWARD"),
                    ("STRAIGHT", "STRAIGHT"))

    voyage = models.CharField(max_length=35)
    vessel = models.ForeignKey(Vessel, on_delete=models.PROTECT, )
    status = models.CharField(max_length=4, choices=STATUS, default='UCMP')
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    arrival_berthed = models.DateTimeField(null=True, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    previous_schedule = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    is_phase_in = models.BooleanField(default=False)
    direction = models.CharField(max_length=25, choices=VOYAGE_DIRECTION, null=True, blank=True,)


    def __str__(self):
        return f'{self.vessel.name} - {self.voyage}'


class PortOfCall(models.Model):
    STATUS = (('ARRIVED', 'ARRIVED'),('NOT ARRIVED','NOT ARRIVED'), 
              ('SAILED', 'SAILED'),('NOT SAILED','NOT SAILED'),
              ('OMITTED', 'OMITTED'))
    PORT_STATUS = (('PHASE IN', 'PHASE IN'),('PHASE OUT','PHASE OUT'),
              ("CUT AND RUN", 'CUT AND RUN'),('ACTIVE','ACTIVE'),
              ('OMITTED', 'OMITTED'))

    port = models.ForeignKey(Port, on_delete=models.PROTECT,
                             related_name='port_of_calls',
                             related_query_name='port_of_calls')
    to_port = models.ForeignKey(Port, on_delete=models.SET_NULL,
                                related_name='from_port_of_calls',
                                related_query_name='from_port_of_calls',
                                null=True, blank=True)
    vessel_schedule = models.ForeignKey(VesselSchedule,
                                        on_delete=models.PROTECT,
                                        related_name='port_of_calls',
                                        related_query_name='port_of_calls')
    eta = models.DateTimeField(null=True, blank=True)
    etd = models.DateTimeField(null=True, blank=True)
    ata = models.DateTimeField(null=True, blank=True)
    atd = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=11, choices=STATUS,
                              default="NOT SAILED")
    port_status = models.CharField(max_length=11, choices=PORT_STATUS,
                              default="ACTIVE")
    call_no = models.CharField(max_length=255, null=True, blank=True)
    via_no = models.CharField(max_length=255, null=True, blank=True)
    via_date = models.DateTimeField(null=True, blank=True)
    port_order = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.vessel_schedule.vessel.name} - {self.vessel_schedule.voyage} | {self.port.name}'


class SlotOpening(models.Model):

    """
    This model is used for defining slot opening.
    """
    OPENING_CRITERIA = (
        ('DEAD', 'Dead Freight contract'),
        ('SEGM', 'Segment Contract'),
        ('SEGMDIR', 'Segment Direct'),
        ('SEGMTHR', 'Segment Through Slot')
    )
    opening_criteria = models.CharField(max_length=10, choices=OPENING_CRITERIA, default='SEGMDIR')
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE)
    vessel_schedule = models.ForeignKey(VesselSchedule,
                                        on_delete=models.CASCADE)
    call_port = models.ForeignKey(PortOfCall,
                                  related_name='slot_openings_port_of_call',
                                  on_delete=models.CASCADE, null=True,
                                  blank=True)
    port = models.ForeignKey(Port, related_name='slot_opening_ports',
                             on_delete=models.CASCADE,
                             null=True, blank=True)
    to_port = models.ForeignKey(Port, related_name='slot_opening_to_ports',
                                on_delete=models.CASCADE, null=True,
                                blank=True)
    to_vessel_schedule = models.ForeignKey(VesselSchedule,
                                        related_name='slot_opening_to_vessel_schedule',
                                        on_delete=models.CASCADE,
                                        null=True, blank=True)
    to_call_port = models.ForeignKey(PortOfCall,
                                       related_name='slot_opening_to_port_of_call',
                                        on_delete=models.CASCADE, null=True,
                                        blank=True)
    operator = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True,
                                 blank=True)
    
    

    def __str__(self):
        return f'{self.vessel.name} - {self.vessel_schedule.voyage} | {self.opening_criteria} | {self.port.name} | {self.to_port.name} | {self.operator.name}'



class SlotWeightStatus(models.Model):
    """
    This model is used for define the number of slots and weight opened, provisioned and used.
    """
    STATUS = (('LADN', 'LADEN'),
              ('TRST', 'TRANSSHIPMENT'),
              ('EMTY', 'EMPTY'))

    slot_opening = models.ForeignKey(SlotOpening, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS, max_length=4, default='LADN')
    total_slots = models.IntegerField(default=0)
    used_slots = models.IntegerField(default=0)
    provisioned_slots = models.IntegerField(default=0)
    total_weight = models.DecimalField(max_digits=11, decimal_places=2,
                                       default=0)
    used_weight = models.DecimalField(max_digits=11, decimal_places=2,
                                      default=0)
    provisioned_weight = models.DecimalField(max_digits=11, decimal_places=2,
                                            default=0)
    
    def __str__(self):
        return f'{self.slot_opening.vessel.name} - {self.slot_opening.vessel_schedule.voyage} | {self.status}'


class SlotContract(models.Model):
    """
    This model is used for define the slot contract.
    """
    OPENING_CRITERIA = (
        ('DEAD', 'Dead Freight contract'),
        ('SEGM', 'Segment Contract'),
        ('SEGMDIR', 'Segment Direct'),
        ('SEGMTHR', 'Segment Through Slot')
    )
    number = models.CharField(max_length=255, unique=True)
    operator = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    contract_criteria = models.CharField(max_length=255, choices=OPENING_CRITERIA)
    slot_rate = models.DecimalField(max_digits=11, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.number} | {self.operator.name} | {self.contract_criteria} | {self.slot_rate}'


class SlotContractVesselScheduleMapping(models.Model):
    """
    This model is used for define the slot contract vessel schedule mapping.
    """
    slot_contract = models.ForeignKey(SlotContract, on_delete=models.CASCADE)
    vessel_schedule = models.ForeignKey(VesselSchedule, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.slot_contract.number} | {self.vessel_schedule.vessel.name} - {self.vessel_schedule.voyage}'
        

class ContractPortPairRate(models.Model):
    """
    This model is used for define the contract port pair rate.
    """
    contract = models.ForeignKey(SlotContract, on_delete=models.CASCADE)
    port = models.ForeignKey(Port, on_delete=models.CASCADE)
    to_port = models.ForeignKey(Port, related_name='contract_port_pair_to_ports', on_delete=models.CASCADE, null=True, blank=True)
    rate = models.DecimalField(max_digits=11, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.contract.number} | {self.port.name} | {self.to_port.name} | {self.rate}'