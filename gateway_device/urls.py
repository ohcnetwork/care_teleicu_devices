from rest_framework.routers import DefaultRouter

from gateway_device.viewsets.open_id import PublicJWKsView

router = DefaultRouter()

router.register("", PublicJWKsView, basename="public-jwks")

urlpatterns = router.urls
