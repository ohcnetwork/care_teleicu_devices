from care.emr.models.base import EMRBaseModel
from django.db import models

from care.emr.models.base import EMRBaseModel


class PositionPreset(EMRBaseModel):
    name = models.CharField(max_length=255)
    camera = models.ForeignKey(
        "emr.Device", on_delete=models.CASCADE, related_name="position_presets"
    )
    location = models.ForeignKey("emr.FacilityLocation", on_delete=models.PROTECT)
    ptz = models.JSONField()
    is_default = models.BooleanField(default=False)
    sort_index = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.sort_index:
            self.sort_index = (
                PositionPreset.objects.filter(location=self.location).aggregate(
                    models.Max("sort_index", default=0)
                )["sort_index__max"]
                + 1
            )
        super().save(*args, **kwargs)
