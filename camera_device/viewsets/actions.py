from drf_spectacular.utils import extend_schema
from pydantic import BaseModel
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import GenericViewSet

from camera_device.spec import PTZPayloadSpec
from care.emr.models.device import Device
from gateway_device.client import GatewayClient


class GotoPresetRequestSpec(BaseModel):
    preset: int | None


class CameraActionsViewSet(GenericViewSet):
    queryset = Device.objects.all()
    lookup_field = "external_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        # TODO: add authzn. here...
        return queryset

    def get_gateway_request_data(self, *args, **kwargs):
        instance = self.get_object()
        metadata = instance.metadata
        try:
            hostname = metadata["endpoint_address"]
            username = metadata["username"]
            password = metadata["password"]
        except KeyError as e:
            raise ValidationError({key: "Not configured" for key in e.args}) from e
        return {
            "hostname": hostname,
            "port": 80,
            "username": username,
            "password": password,
            **kwargs,
        }

    def get_gateway_client(self):
        instance = self.get_object()
        metadata = instance.metadata

        try:
            gateway_external_id = metadata["gateway"]
            gateway_device = Device.objects.get(
                external_id=gateway_external_id, care_type="gateway"
            )
        except KeyError as e:
            raise ValidationError({key: "Not configured" for key in e.args}) from e
        except Device.DoesNotExist as e:
            raise ValidationError("Gateway not found") from e

        return GatewayClient(gateway_device)

    @action(detail=True, methods=["GET"])
    def get_status(self, request, *args, **kwargs):
        gateway_client = self.get_gateway_client()
        request_data = self.get_gateway_request_data()
        return gateway_client.get("/status", request_data, as_http_response=True)

    @action(detail=True, methods=["GET"])
    def get_presets(self, request, *args, **kwargs):
        gateway_client = self.get_gateway_client()
        request_data = self.get_gateway_request_data()
        return gateway_client.get("/presets", request_data, as_http_response=True)

    @extend_schema(request=GotoPresetRequestSpec)
    @action(detail=True, methods=["POST"])
    def goto_preset(self, request, *args, **kwargs):
        gateway_client = self.get_gateway_client()
        validated_data = GotoPresetRequestSpec(**request.data).model_dump(mode="json")
        request_data = self.get_gateway_request_data(**validated_data)
        return gateway_client.post("/gotoPreset", request_data, as_http_response=True)

    @extend_schema(request=PTZPayloadSpec)
    @action(detail=True, methods=["POST"])
    def absolute_move(self, request, *args, **kwargs):
        gateway_client = self.get_gateway_client()
        validated_data = PTZPayloadSpec(**request.data).model_dump(mode="json")
        request_data = self.get_gateway_request_data(**validated_data)
        return gateway_client.post("/absoluteMove", request_data, as_http_response=True)

    @extend_schema(request=PTZPayloadSpec)
    @action(detail=True, methods=["POST"])
    def relative_move(self, request, *args, **kwargs):
        gateway_client = self.get_gateway_client()
        validated_data = PTZPayloadSpec(**request.data).model_dump(mode="json")
        request_data = self.get_gateway_request_data(**validated_data)
        return gateway_client.post("/relativeMove", request_data, as_http_response=True)

    @action(detail=True, methods=["GET"])
    def stream_token(self, request, *args, **kwargs):
        instance = self.get_object()
        metadata = instance.metadata
        gateway_client = self.get_gateway_client()
        try:
            request_data = {"stream_id": metadata["stream_id"]}
        except KeyError as e:
            raise ValidationError({key: "Not configured" for key in e.args}) from e
        return gateway_client.post(
            "/api/stream/getToken/videoFeed", request_data, as_http_response=True
        )
