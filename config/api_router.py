from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from democrasite.users.api.views import UserViewSet
from democrasite.webiscite.api.views import BillViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("bills", BillViewSet)

# Unfortunately if we want automatical links for models we can't use a namespace
# but I may reconsider anyway
# app_name = "api"  # noqa: ERA001
urlpatterns = router.urls
