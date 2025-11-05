from drf_spectacular.utils import extend_schema
from pydantic import BaseModel
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import GenericViewSet

from care.emr.models.device import Device
from care.emr.models.diagnostic_report import DiagnosticReport
from care.emr.models.observation_definition import ObservationDefinition
from care.emr.resources.diagnostic_report.spec import (
    DiagnosticReportRetrieveSpec,
)

from gateway_device.client import GatewayClient

class LabAnalyzerActionsViewSet(GenericViewSet):
    queryset = Device.objects.filter(care_type="lab-analyzer")
    lookup_field = "external_id"

    def get_gateway_request_data(self, *args, **kwargs):
        instance = self.get_object()
        metadata = instance.metadata
        try:
            hostname = metadata["endpoint_address"]
            port = metadata["port"]
            type = metadata["type"]
        except KeyError as e:
            raise ValidationError({key: "Not configured" for key in e.args}) from e
        return {
            "hostname": hostname,
            "port": port,
            "type": type,
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
        return gateway_client.get("/lab_analyzer/status", request_data, as_http_response=True)

    @action(detail=True, methods=["POST"])
    def order_test(self, request, *args, **kwargs):
        gateway_client = self.get_gateway_client()
        payload = {}
        diagnostic_report = request.data.get("diagnostic_report")
        if not diagnostic_report:
            raise ValidationError({"diagnostic_report": "This field is required."})
        diagnostic_report_instance = DiagnosticReport.objects.get(
            external_id=diagnostic_report
        )
        diagnostic_report = DiagnosticReportRetrieveSpec.serialize(
            diagnostic_report_instance
        ).to_json()

        request_data = self.get_gateway_request_data(payload=payload)
        return gateway_client.post("/lab_analyzer/order_test", request_data, as_http_response=True)

    @action(detail=True, methods=["GET"])
    def get_results(self, request, *args, **kwargs):
        gateway_client = self.get_gateway_client()
        request_data = self.get_gateway_request_data(json=request.data)
        return gateway_client.get("/lab_analyzer/get_results", request_data, as_http_response=True)

    @action(detail=True, methods=["POST"])
    def clear_results(self, request, *args, **kwargs):
        gateway_client = self.get_gateway_client()
        request_data = self.get_gateway_request_data(json=request.data)
        return gateway_client.post("/lab_analyzer/clear_results", request_data, as_http_response=True)

