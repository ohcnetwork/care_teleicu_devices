from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models import Device
from django_filters import rest_framework as filters
from rest_framework.generics import get_object_or_404

from camera_device.models import PositionPreset
from camera_device.spec import (
    PositionPresetReadSpec,
    PositionPresetCreateSpec,
    PositionPresetUpdateSpec,
)


class PositionPresetFilters(filters.FilterSet):
    location = filters.UUIDFilter(field_name="location", lookup_expr="exact")


class CameraPositionPresetViewSet(EMRModelViewSet):
    database_model = PositionPreset
    pydantic_model = PositionPresetCreateSpec
    pydantic_update_model = PositionPresetUpdateSpec
    pydantic_retrieve_model = PositionPresetReadSpec
    pydantic_read_model = PositionPresetReadSpec
    filterset_class = PositionPresetFilters
    filter_backends = (filters.DjangoFilterBackend,)

    def get_queryset(self):
        camera = self.get_camera_obj()
        queryset = super().get_queryset().filter(camera=camera)
        # TODO: add authzn. here...
        return queryset

    def get_camera_obj(self):
        return get_object_or_404(
            Device, external_id=self.kwargs["camera_external_id"], care_type="camera"
        )

    def clean_create_data(self, request_data):
        camera = self.get_camera_obj()
        request_data["camera"] = camera.external_id
        return request_data
