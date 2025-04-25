import enum
from pydantic import BaseModel, UUID4, field_validator

from camera_device.models.position_preset import PositionPreset
from care.emr.models import Device, FacilityLocation
from care.emr.resources.base import EMRResource
from care.emr.resources.location.spec import FacilityLocationRetrieveSpec
from pydantic import BaseModel, UUID4, field_validator

from camera_device.models.position_preset import PositionPreset
from gateway_device.spec import GatewayDeviceReadSpec
from gateway_device.utils import validate_endpoint_address


class CameraDeviceTypes(enum.Enum):
    onvif = "ONVIF"


class CameraDeviceMetadataWriteSpec(BaseModel):
    type: CameraDeviceTypes | None = None
    gateway: UUID4 | None = None
    endpoint_address: str | None = None
    username: str | None = None
    password: str | None = None
    stream_id: str | None = None

    @field_validator("gateway", mode="before")
    @classmethod
    def validate_gateway(cls, value):
        if value is None:
            return value
        try:
            Device.objects.get(external_id=value, care_type="gateway")
        except Device.DoesNotExist:
            raise ValueError("Gateway device does not exist")
        return value

    @field_validator("endpoint_address", mode="before")
    @classmethod
    def validate_endpoint_address(cls, value):
        if value is None:
            return None
        return validate_endpoint_address(value)


class CameraDeviceMetadataReadSpec(BaseModel):
    gateway: GatewayDeviceReadSpec | None = None
    type: CameraDeviceTypes | None = None
    endpoint_address: str | None = None
    username: str | None = None
    password: str | None = None
    stream_id: str | None = None


class PTZPayloadSpec(BaseModel):
    x: float
    y: float
    zoom: float


MIN_SORT_INDEX = 0
MAX_SORT_INDEX = 10000


class PositionPresetBaseSpec(EMRResource):
    __model__ = PositionPreset
    __exclude__ = ["camera", "location"]

    id: UUID4 | None = None
    name: str
    ptz: PTZPayloadSpec
    sort_index: int | None = Field(
        default=0,
        ge=MIN_SORT_INDEX,
        le=MAX_SORT_INDEX,
    )


class PositionPresetReadSpec(PositionPresetBaseSpec):
    location: FacilityLocationRetrieveSpec
    is_default : bool

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        cls.serialize_audit_users(mapping, obj)
        mapping["location"] = FacilityLocationRetrieveSpec.serialize(
            obj.location
        ).to_json()


class PositionPresetUpdateSpec(PositionPresetBaseSpec):
    location: UUID4

    def perform_extra_deserialization(self, is_update, obj):
        try:
            obj.location = FacilityLocation.objects.get(external_id=self.location)
        except FacilityLocation.DoesNotExist:
            raise ValueError("Location does not exist")


class PositionPresetCreateSpec(PositionPresetUpdateSpec):
    camera: UUID4

    def perform_extra_deserialization(self, is_update, obj):
        super().perform_extra_deserialization(is_update, obj)
        obj.camera = Device.objects.get(external_id=self.camera, care_type="camera")
