from care.emr.registries.device_type.device_registry import DeviceTypeBase
from gateway_device.spec import (
    GatewayDeviceMetadataWriteSpec,
    GatewayDeviceMetadataReadSpec,
)


class GatewayDevice(DeviceTypeBase):
    def handle_create(self, request_data, obj):
        validated_data = GatewayDeviceMetadataWriteSpec(**request_data)
        obj.metadata = validated_data.model_dump(mode="json")
        obj.save(update_fields=["metadata"])
        return obj

    def handle_update(self, request_data, obj):
        validated_data = GatewayDeviceMetadataWriteSpec(**request_data)
        obj.metadata = validated_data.model_dump(mode="json")
        obj.save(update_fields=["metadata"])
        return obj

    def list(self, obj):
        return self.retrieve(obj)

    def retrieve(self, obj):
        return GatewayDeviceMetadataReadSpec(**obj.metadata).model_dump(mode="json")

    def perform_action(self, obj, action, request):
        # TODO: return BadRequest / Not Allowed
        raise NotImplementedError("Gateway device actions are not implemented")
