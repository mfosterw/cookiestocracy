from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from democrasite.users.api.views import UserViewSet
from democrasite.webiscite.api.views import BillViewSet, PullRequestViewSet

router: SimpleRouter | DefaultRouter
if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("bills", BillViewSet)
router.register("pull-requests", PullRequestViewSet)

# Unfortunately if we want to automatically create links between models we can't use a namespace
# app_name = "api"
urlpatterns = router.urls
