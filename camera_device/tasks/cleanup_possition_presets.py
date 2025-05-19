from logging import Logger

from celery import shared_task
from celery.utils.log import get_task_logger

from camera_device.models import PositionPreset

logger: Logger = get_task_logger(__name__)


@shared_task
def cleanup_possition_presets():
    """
    Deletes PositionPreset objects whose associated FacilityLocation has been deleted.
    """
    logger.info("Cleaning up PositionPreset objects with deleted FacilityLocation")
    queryset = PositionPreset.objects.filter(location__deleted=True)
    queryset.delete()
