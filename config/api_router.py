from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from democrasite.users.api.views import UserViewSet
from democrasite.webiscite.api.views import BillViewSet

router: SimpleRouter | DefaultRouter
if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("bills", BillViewSet)


app_name = "api"
urlpatterns = router.urls
