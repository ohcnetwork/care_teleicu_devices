from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from lab_analyzer_device.viewsets.actions import LabAnalyzerActionsViewSet
from lab_analyzer_device.viewsets.automation import LabAnalyzerAutomationViewSet


router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("actions", LabAnalyzerActionsViewSet, basename="lab-analyzer-actions")
router.register("automation", LabAnalyzerAutomationViewSet, basename="lab-analyzer-automation")

urlpatterns = router.urls
