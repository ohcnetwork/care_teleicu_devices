from care.emr.models.base import EMRBaseModel
from django.db import models


class PositionPreset(EMRBaseModel):
    name = models.CharField(max_length=255)
    camera = models.ForeignKey("emr.Device", on_delete=models.CASCADE)
    location = models.ForeignKey("emr.FacilityLocation", on_delete=models.PROTECT)
    ptz = models.JSONField()
