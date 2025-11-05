from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

PLUGIN_NAME = "lab_analyzer_device"


class LabAnalyzerDeviceConfig(AppConfig):
    name = PLUGIN_NAME
    verbose_name = _("Lab Analyzer Device")

    def ready(self):
        """
        Import models, signals, and other dependencies here to ensure
        Django's app registry is fully initialized before use.
        """
        from care.emr.registries.device_type.device_registry import DeviceTypeRegistry
        from lab_analyzer_device.device import LabAnalyzerDevice
        from lab_analyzer_device import signals  # noqa: F401

        DeviceTypeRegistry.register("lab-analyzer", LabAnalyzerDevice)
