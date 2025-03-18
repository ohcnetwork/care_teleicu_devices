from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

PLUGIN_NAME = "gateway_device"


class GatewayDeviceConfig(AppConfig):
    name = PLUGIN_NAME
    verbose_name = _("Gateway Device")

    def ready(self):
        """
        Import models, signals, and other dependencies here to ensure
        Django's app registry is fully initialized before use.
        """
        from care.emr.registries.device_type.device_registry import DeviceTypeRegistry
        from gateway_device.device import GatewayDevice

        DeviceTypeRegistry.register("gateway", GatewayDevice)
