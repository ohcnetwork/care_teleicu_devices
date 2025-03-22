import enum
from pydantic import BaseModel, field_validator, UUID4

from care.emr.models.device import Device
from gateway_device.spec import GatewayDeviceReadSpec
from gateway_device.utils import validate_endpoint_address


class VitalsObservationDeviceType(enum.Enum):
    hl7_monitor = "HL7-Monitor"
    ventilator = "Ventilator"


class VitalsObservationDeviceMetadataReadSpec(BaseModel):
    type: VitalsObservationDeviceType
    gateway: GatewayDeviceReadSpec | None = None
    endpoint_address: str | None = None


class VitalsObservationDeviceMetadataWriteSpec(BaseModel):
    type: VitalsObservationDeviceType
    gateway: UUID4 | None = None
    endpoint_address: str | None = None

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
