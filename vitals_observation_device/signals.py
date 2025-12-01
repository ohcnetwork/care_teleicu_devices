from django.db.models.signals import post_save
from django.dispatch import receiver

from care.emr.models import FacilityLocation, Device


@receiver(post_save, sender=FacilityLocation)
def unlink_on_encounter_location_end(sender, instance, created, **kwargs):
    """
    Signal handler to unlink vitals observation device from the encounter
    when the bed (location) is no longer associated with the same encounter
    as the device.
    """
    devices_to_unlink = Device.objects.filter(
        care_type="vitals-observation", current_location=instance
    ).exclude(current_encounter=instance.current_encounter)
    devices_to_unlink.update(current_encounter=None)
