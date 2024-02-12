from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from democrasite.users.api.views import UserViewSet

router: SimpleRouter | DefaultRouter
if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)


app_name = "api"
urlpatterns = router.urls
