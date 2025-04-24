from django_filters import rest_framework as filters
from rest_framework import filters as rest_framework_filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404

from camera_device.models import PositionPreset
from camera_device.spec import (
    PositionPresetReadSpec,
    PositionPresetCreateSpec,
    PositionPresetUpdateSpec,
)
from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models import Device, FacilityLocation
from care.security.authorization import AuthorizationController


class PositionPresetFilters(filters.FilterSet):
    location = filters.UUIDFilter(
        field_name="location__external_id", lookup_expr="exact"
    )


class CameraPositionPresetViewSet(EMRModelViewSet):
    database_model = PositionPreset
    pydantic_model = PositionPresetCreateSpec
    pydantic_update_model = PositionPresetUpdateSpec
    pydantic_retrieve_model = PositionPresetReadSpec
    pydantic_read_model = PositionPresetReadSpec
    filterset_class = PositionPresetFilters
    filter_backends = (
        filters.DjangoFilterBackend,
        rest_framework_filters.OrderingFilter,
    )
    ordering_fields = ["sort_index", "location__name"]

    def authorize_create(self, instance):
        device = self.get_camera_obj()
        if not AuthorizationController.call(
            "can_manage_device", self.request.user, device
        ):
            raise PermissionDenied("You do not have permission to update device")

    def authorize_update(self, instance, model_instance):
        self.authorize_create(instance)

    def authorize_destroy(self, instance):
        self.authorize_update(None, instance)

    def get_queryset(self):
        device = self.get_camera_obj()
        queryset = super().get_queryset().filter(camera=device)

        if "location" in self.request.GET:
            location = get_object_or_404(
                FacilityLocation, external_id=self.request.GET["location"]
            )
            if not AuthorizationController.call(
                "can_read_devices_on_location", self.request.user, location
            ):
                raise PermissionDenied(
                    "You do not have permission to get position presets of this location"
                )
        else:
            if not AuthorizationController.call(
                "can_read_device", self.request.user, device
            ):
                raise PermissionDenied("You do not have permission to update device")

        return queryset

    def get_camera_obj(self):
        return get_object_or_404(
            Device, external_id=self.kwargs["camera_external_id"], care_type="camera"
        )

    def clean_create_data(self, request_data):
        camera = self.get_camera_obj()
        request_data["camera"] = camera.external_id
        return request_data
