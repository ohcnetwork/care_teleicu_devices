import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from gateway_device.client import GatewayClient
from rest_framework.exceptions import ValidationError

from care.emr.models.device import Device
from care.emr.models.service_request import ServiceRequest
from care.emr.models.specimen import Specimen
from care.emr.models.observation_definition import ObservationDefinition

logger = logging.getLogger(__name__)


def make_device_request(instance, payload):
    def get_gateway_client():
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

    def get_gateway_request_data(*args, **kwargs):
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

    request_data = get_gateway_request_data(payload=payload)
    logger.info(f"Making device request with data: {request_data}")
    gateway_client = get_gateway_client()
    return gateway_client.post(
        "/lab_analyzer/order_test", request_data, as_http_response=True
    )


@receiver(post_save, sender=Specimen)
def enqueue_diagnostic_report_processing(sender, instance, created, **kwargs):
    logger.debug(f"Specimen post_save signal received for id: {instance.id}")
    if created or instance.deleted or instance.status != "available":
        return

    if instance.collection and instance.collection.get("collected_date_time"):
        try:
            service_request: ServiceRequest = instance.service_request
            locations = service_request.locations
            if (
                service_request.healthcare_service
                and service_request.healthcare_service.locations
            ):
                locations.append(service_request.healthcare_service.locations)
            if locations:
                device = Device.objects.filter(
                    current_location__in=locations,
                    care_type="lab-analyzer",
                ).first()
                if not device:
                    logger.warning("No lab analyzer device found for location")
                    return
            else:
                logger.warning(
                    f"Service request {service_request.id} has no healthcare service or locations"
                )
                return

            encounter = service_request.encounter
            patient = encounter.patient
            facility = service_request.facility
            activity_definition = service_request.activity_definition
            observation_definition = ObservationDefinition.objects.filter(
                id__in=activity_definition.observation_result_requirements
            ).first()

            payload = {
                "patient": {
                    "external_id": str(patient.external_id),
                    "name": patient.name,
                    "date_of_birth": patient.date_of_birth.isoformat()
                    if patient.date_of_birth
                    else None,
                    "gender": patient.gender,
                },
                "facility": {
                    "external_id": str(facility.external_id),
                    "name": facility.name,
                },
                "service_request": {
                    "external_id": str(service_request.external_id),
                    "test_code": observation_definition.code,
                    "date_time": service_request.created_date.isoformat(),
                },
            }
            response = make_device_request(device, payload)
            logger.info(
                f"Lab analyzer request sent for Specimen {instance.id}, response status: {response.status_code}"
            )

        except Exception as e:
            logger.error(
                f"Error processing Specimen {instance.id} for lab analyzer: {str(e)}", exc_info=True
            )


# def generate_value_for_component(component):
#     # generate random value for component based on its type
#     value = None
#     if component["permitted_data_type"] == "boolean":
#         value = True
#     elif component["permitted_data_type"] in ["quantity", "integer", "decimal"]:
#         value = random.randint(1, 100)
#     elif component["permitted_data_type"] == "string":
#         value = "test result"

#     logger.info(
#         f"Generated value for component {component['code']['code']}: {value} {component.get('permitted_unit', None)}"
#     )

#     return {
#         "value": {
#             "value": value,
#             "unit": component.get("permitted_unit", None),
#         },
#         "code": component["code"],
#         "reference_range": component.get("qualified_ranges", []),
#     }


# @receiver(post_save, sender=DiagnosticReport)
# def diagnostic_report_post_save(sender, instance, created, **kwargs):
#     if not created:
#         pass

#     logger.info(
#         f"DiagnosticReport created with id: {instance.id}, external_id: {instance.external_id}"
#     )

#     care_user, _ = User.objects.get_or_create(
#         username="careuser",
#         defaults={
#             "first_name": "Care",
#             "last_name": "User",
#             "user_type": "care_user",
#             "email": "careuser@ohc.network",
#             "phone_number": "",
#             "is_active": False,
#         },
#     )

#     observation_definitions_ids = (
#         instance.service_request.activity_definition.observation_result_requirements
#     )

#     metrics_cache = {}
#     for observation_definition in ObservationDefinition.objects.filter(
#         id__in=observation_definitions_ids
#     ):
#         component = []
#         for c in observation_definition.component:
#             component.append(generate_value_for_component(c))
#         observation_obj = Observation(
#             main_code=observation_definition.code,
#             status=ObservationStatus.final.value,
#             encounter=instance.encounter,
#             category=observation_definition.category,
#             observation_definition=observation_definition,
#             created_by=care_user,
#             updated_by=care_user,
#             patient=instance.patient,
#             subject_id=instance.encounter.external_id,
#             diagnostic_report=instance,
#             subject_type=SubjectType.encounter.value,
#             component=component,
#             effective_datetime=now(),
#             interpretation="normal",
#             value_type="quantity",
#             value={"value": ""},
#         )

#         if observation_obj.observation_definition:
#             returned_cache = compute_observation_interpretation(
#                 observation_obj, metrics_cache
#             )
#             metrics_cache = returned_cache
#         observation_obj.save()
#         logger.info(
#             f"Observation created with id: {observation_obj.id}, external_id: {observation_obj.external_id}"
#         )
#         time.sleep(5)  # To ensure unique timestamps for observations
