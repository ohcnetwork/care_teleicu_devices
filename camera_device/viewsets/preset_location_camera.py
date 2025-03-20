from care.emr.api.viewsets.base import EMRModelReadOnlyViewSet
from care.emr.models import Device
from care.emr.models import FacilityLocation
from care.emr.resources.device.spec import (
    DeviceListSpec,
    DeviceRetrieveSpec,
)
from care.security.authorization import AuthorizationController
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404


class PresetLocationCameraViewSet(EMRModelReadOnlyViewSet):
    database_model = Device
    pydantic_read_model = DeviceListSpec
    pydantic_retrieve_model = DeviceRetrieveSpec

    def get_location_obj(self):
        return get_object_or_404(
            FacilityLocation, external_id=self.kwargs["location_external_id"]
        )

    def get_queryset(self):
        location = self.get_location_obj()
        if not AuthorizationController.call(
            "can_read_devices_on_location", self.request.user, location
        ):
            raise PermissionDenied(
                "You do not have permission to get devices of this location."
            )
        return (
            super()
            .get_queryset()
            .filter(
                care_type="camera",
                position_presets__location=self.get_location_obj(),
            )
            .distinct("id")
        )
