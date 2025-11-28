import enum
from pydantic import BaseModel, Field, field_validator, UUID4, model_validator

from care.emr.models.device import Device
from gateway_device.spec import GatewayDeviceReadSpec
from gateway_device.utils import validate_endpoint_address


class LabAnalyzerDeviceType(enum.Enum):
    hl7_2_over_ip = "hl7_2_over_ip"



class LabResultPayloadSpec(BaseModel):
    message: str


class LabAnalyzerDeviceMetadataReadSpec(BaseModel):
    type: LabAnalyzerDeviceType
    gateway: GatewayDeviceReadSpec | None = None
    endpoint_address: str | None = None
    port: int | None = None


class LabAnalyzerDeviceMetadataWriteSpec(BaseModel):
    type: LabAnalyzerDeviceType
    gateway: UUID4 | None = None
    endpoint_address: str | None = None
    port: int | None = Field(None, ge=80, le=65535)

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

    @model_validator(mode='after')
    def validate_endpoint_and_port(self):
        if (self.endpoint_address is None) != (self.port is None):
            raise ValueError("Both endpoint_address and port must be provided together or both must be None")

        if self.endpoint_address is not None:
            self.endpoint_address = validate_endpoint_address(self.endpoint_address)

        if self.port is not None:
            if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
                raise ValueError("Port must be between 1 and 65535")

        return self
