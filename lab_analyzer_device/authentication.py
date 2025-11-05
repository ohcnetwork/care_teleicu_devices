import logging

import jwt
import requests
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.tokens import Token

from care.emr.models import Device
from care.users.models import User

logger = logging.getLogger(__name__)


OPENID_REQUEST_TIMEOUT = 5


def jwk_response_cache_key(url: str) -> str:
    return f"jwk_response:{url}"


class MiddlewareAuthentication(JWTAuthentication):
    """
    An authentication plugin that authenticates requests through a JSON web
    token provided in a request header.
    """

    gateway_header = "X-Gateway-Id"
    auth_header_type = "Middleware_Bearer"
    auth_header_type_bytes = auth_header_type.encode(HTTP_HEADER_ENCODING)

    def get_public_key(self, url):
        public_key_json = cache.get(jwk_response_cache_key(url))
        if not public_key_json:
            res = requests.get(url, timeout=OPENID_REQUEST_TIMEOUT)
            res.raise_for_status()
            public_key_json = res.json()
            cache.set(jwk_response_cache_key(url), public_key_json, timeout=60 * 5)
        return public_key_json["keys"][0]

    def open_id_authenticate(self, url, token):
        public_key_response = self.get_public_key(url)
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(public_key_response)
        return jwt.decode(token, key=public_key, algorithms=["RS256"])

    def authenticate_header(self, request):
        return f'{self.auth_header_type} realm="{self.www_authenticate_realm}"'

    def get_user(self, _: Token):
        care_user, _ = User.objects.get_or_create(
            username="careuser",
            defaults={
                "first_name": "Care",
                "last_name": "User",
                "user_type": "care_user",
                "email": "careuser@ohc.network",
                "phone_number": "",
                "is_active": False,
            },
        )
        return care_user

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None or self.gateway_header not in request.headers:
            return None

        external_id = request.headers[self.gateway_header]

        try:
            gateway = Device.objects.get(external_id=external_id, care_type="gateway")
        except (Device.DoesNotExist, ValidationError) as e:
            raise InvalidToken(
                {"detail": "Invalid Gateway Device", "messages": []}
            ) from e

        if not gateway.metadata and not gateway.metadata.get("endpoint_address"):
            raise InvalidToken({"detail": "Gateway endpoint not configured"})

        protocol = "https" if gateway.metadata.get("use_https", True) else "http"

        open_id_url = f"{protocol}://{gateway.metadata['endpoint_address']}/.well-known/openid-configuration/"

        validated_token = self.get_validated_token(open_id_url, raw_token)

        return self.get_user(validated_token), validated_token

    def get_raw_token(self, header):
        """
        Extracts an un-validated JSON web token from the given "Authorization"
        header value.
        """
        parts = header.split()

        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if parts[0] != self.auth_header_type_bytes:
            # Assume the header does not contain a JSON web token
            return None

        if len(parts) != 2:  # noqa: PLR2004
            raise AuthenticationFailed(
                _("Authorization header must contain two space-delimited values"),
                code="bad_authorization_header",
            )

        return parts[1]

    def get_validated_token(self, url, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        try:
            return self.open_id_authenticate(url, raw_token)
        except Exception as e:
            logger.info(e, "Token: ", raw_token)

        raise InvalidToken({"detail": "Given token not valid for any token type"})


# class MiddlewareAssetAuthentication(MiddlewareAuthentication):
#     def get_user(self, validated_token, facility):
#         """
#         Attempts to find and return a user using the given validated token.
#         """
#         if "asset_id" not in validated_token:
#             raise InvalidToken({"detail": "Given token does not contain asset_id"})

#         try:
#             asset_obj = Asset.objects.select_related("current_location__facility").get(
#                 external_id=validated_token["asset_id"]
#             )
#         except (Asset.DoesNotExist, ValidationError) as e:
#             raise InvalidToken(
#                 {"detail": "Invalid Asset ID", "messages": [str(e)]}
#             ) from e

#         if asset_obj.current_location.facility != facility:
#             raise InvalidToken({"detail": "Facility not connected to Asset"})

#         # Create/Retrieve User and return them
#         asset_user = User.objects.filter(asset=asset_obj).first()
#         if not asset_user:
#             password = User.objects.make_random_password()
#             asset_user = User(
#                 username=f"asset{asset_obj.external_id!s}",
#                 email="support@ohc.network",
#                 password=f"{password}xyz",  # The xyz makes it inaccessible without hashing
#                 gender=3,
#                 phone_number="919999999999",
#                 user_type=User.TYPE_VALUE_MAP["Nurse"],
#                 verified=True,
#                 asset=asset_obj,
#                 date_of_birth=timezone.now().date(),
#             )
#             asset_user.save()
#         return asset_user


class MiddlewareAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "config.authentication.MiddlewareAuthentication"
    name = "middlewareAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": _(
                "Used for authenticating requests from the middleware. "
                "The scheme requires a valid JWT token in the Authorization header "
                "along with the facility id in the X-Facility-Id header. "
                "--The value field is just for preview, filling it will show allowed "
                "endpoints.--"
            ),
        }


# class MiddlewareAssetAuthenticationScheme(OpenApiAuthenticationExtension):
#     target_class = "config.authentication.MiddlewareAssetAuthentication"
#     name = "middlewareAssetAuth"

#     def get_security_definition(self, auto_schema):
#         return {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT",
#             "description": _(
#                 "Used for authenticating requests from the middleware on behalf of assets. "
#                 "The scheme requires a valid JWT token in the Authorization header "
#                 "along with the facility id in the X-Facility-Id header. "
#                 "--The value field is just for preview, filling it will show allowed "
#                 "endpoints.--"
#             ),
#         }
