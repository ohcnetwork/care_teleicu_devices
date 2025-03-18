import json
import requests
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from care.emr.models.device import Device
from gateway_device.token_generator import generate_jwt


class GatewayClient:
    auth_header_type = "Care_Bearer"

    def __init__(self, gateway: Device):
        self.timeout = settings.PLUGIN_CONFIGS["gateway_device"].get("timeout", 30)
        try:
            self.gateway_host = gateway.metadata["endpoint_address"]
        except KeyError:
            raise ValidationError("Gateway endpoint address not set")
        self.insecure_connection = gateway.metadata.get("insecure_connection", False)
        if settings.IS_PRODUCTION:
            self.insecure_connection = False

    def _get_url(self, endpoint):
        protocol = "http" if self.insecure_connection else "https"
        return f"{protocol}://{self.gateway_host}{endpoint}"

    def _get_headers(self):
        return {
            "Authorization": f"{self.auth_header_type} {generate_jwt()}",
            "Accept": "application/json",
        }

    def _validate_response(self, response: requests.Response, as_http_response=False):
        try:
            if as_http_response:
                return HttpResponse(
                    response.content,
                    content_type=response.headers["content-type"],
                    status=response.status_code,
                )
            if response.status_code >= status.HTTP_400_BAD_REQUEST:
                raise APIException(response.text, response.status_code)
            return response.json()
        except requests.Timeout as e:
            raise APIException({"error": "Request Timeout"}, 504) from e
        except json.decoder.JSONDecodeError as e:
            raise APIException(
                {"error": "Invalid Response"}, response.status_code
            ) from e

    def get(self, endpoint, data=None, as_http_response=False):
        url = self._get_url(endpoint)
        response = requests.get(url, params=data, headers=self._get_headers())
        return self._validate_response(response, as_http_response=as_http_response)

    def post(self, endpoint, data=None, as_http_response=False):
        url = self._get_url(endpoint)
        response = requests.post(url, json=data, headers=self._get_headers())
        return self._validate_response(response, as_http_response=as_http_response)
