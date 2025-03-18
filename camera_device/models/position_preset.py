from django.db import models

from care.emr.models import EMRBaseModel


class PositionPreset(EMRBaseModel):
    name = models.CharField(max_length=255)
    camera = models.ForeignKey("emr.Device", on_delete=models.CASCADE)
    location = models.ForeignKey(
        "emr.FacilityLocation", on_delete=models.SET_NULL, null=True
    )
    ptz = models.JSONField()
