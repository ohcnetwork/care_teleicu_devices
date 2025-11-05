import re
from rest_framework.response import Response
from pydantic import UUID4, BaseModel
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import GenericViewSet

from care.emr.models.device import Device
from care.emr.models import DiagnosticReport, ServiceRequest
from care.emr.models.observation_definition import ObservationDefinition
from care.emr.resources.diagnostic_report.spec import (
    DiagnosticReportStatusChoices,
)
from care.emr.resources.observation.spec import ObservationUpdateSpec
from care.emr.resources.observation_definition.observation import (
    convert_od_to_observation,
)
from care.emr.resources.questionnaire.spec import SubjectType
from care.emr.utils.compute_observation_interpretation import (
    compute_observation_interpretation,
)
from care.utils.shortcuts import get_object_or_404

from gateway_device.client import GatewayClient
from lab_analyzer_device.authentication import MiddlewareAuthentication


class UploadObservationRequestSpec(BaseModel):
    service_request: UUID4
    result: ObservationUpdateSpec


class LabAnalyzerAutomationViewSet(GenericViewSet):
    queryset = Device.objects.filter(care_type="lab-analyzer")
    lookup_field = "external_id"
    authentication_classes = [MiddlewareAuthentication]

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

    @action(detail=False, methods=["POST"])
    def create_observation(self, request, *args, **kwargs):

        """ 
        {
            "service_request": "bc7f6758-ee9f-4b91-a1df-f28b578a4572",
            "result": {
                "interpretation": "normal",
                "component": [
                    {
                        "code": {
                            "code": "LP32067-8",
                            "system": "http://loinc.org",
                            "display": "Hemoglobin",
                        },
                        "value": {
                            "value": "11.83",
                            "unit": {
                                "code": "g/dL",
                                "system": "http://unitsofmeasure.org",
                                "display": "g/dL",
                            },
                        },
                        "interpretation": "normal",
                    },
                    {
                        "code": {
                            "code": "LP15101-6",
                            "system": "http://loinc.org",
                            "display": "Hematocrit",
                        },
                        "value": {
                            "value": "45.24",
                            "unit": {
                                "code": "%",
                                "system": "http://unitsofmeasure.org",
                                "display": "%",
                            },
                        },
                        "interpretation": "normal",
                    },
                    {
                        "code": {
                            "code": "LA12896-9",
                            "system": "http://loinc.org",
                            "display": "Erythrocytes",
                        },
                        "value": {
                            "value": "5.58",
                            "unit": {
                                "code": "10*6/uL",
                                "system": "http://unitsofmeasure.org",
                                "display": "10*6/uL",
                            },
                        },
                        "interpretation": "normal",
                    },
                    {
                        "code": {
                            "code": "LP7631-7",
                            "system": "http://loinc.org",
                            "display": "Platelets",
                        },
                        "value": {
                            "value": "367.08",
                            "unit": {
                                "code": "10*3/uL",
                                "system": "http://unitsofmeasure.org",
                                "display": "10*3/uL",
                            },
                        },
                        "interpretation": "normal",
                    },
                ],
            },
        }
        """

        request_data = UploadObservationRequestSpec(**request.data)
        service_request = get_object_or_404(
            ServiceRequest.objects.select_related("activity_definition"), external_id=request_data.service_request
        )

        try:
            diagnostic_report_code = service_request.activity_definition.diagnostic_report_codes[0]
            observation_definition = get_object_or_404(
                ObservationDefinition,
                id=service_request.activity_definition.observation_result_requirements[0],
            )

            diagnostic_report, _ = DiagnosticReport.objects.get_or_create(
                service_request=service_request,
                defaults={
                    "status": DiagnosticReportStatusChoices.final.value,
                    "encounter_id": service_request.encounter_id,
                    "patient_id": service_request.patient_id,
                    "created_by": request.user,
                    "updated_by": request.user,
                    "category":{"code":"LAB","display":"Laboratory","system":"http://terminology.hl7.org/CodeSystem/v2-0074"},
                    "code":diagnostic_report_code
                },
            )

            observation_obj = convert_od_to_observation(
                    observation_definition, diagnostic_report.encounter
            )
            serializer_obj = ObservationUpdateSpec.model_validate(
               request_data.result.model_dump(mode="json")
            )
            model_instance = serializer_obj.de_serialize(obj=observation_obj)
            model_instance.observation_definition = observation_definition
            model_instance.created_by = self.request.user
            model_instance.updated_by = self.request.user
            model_instance.encounter = diagnostic_report.encounter
            model_instance.patient = diagnostic_report.patient
            model_instance.subject_id = diagnostic_report.encounter.external_id
            model_instance.diagnostic_report = diagnostic_report
            model_instance.subject_type = SubjectType.encounter.value
            metrics_cache = {}
            if model_instance.observation_definition:
                returned_cache = compute_observation_interpretation(
                    model_instance, metrics_cache
                )
                metrics_cache = returned_cache
            model_instance.save()
            return Response({"detail": "Observation created successfully"})
        except Exception as e:
            raise ValidationError("Error creating Diagnostic Report") from e