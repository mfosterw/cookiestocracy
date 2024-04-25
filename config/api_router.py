from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import token_refresh

from democrasite.users.api.views import GitHubLogin
from democrasite.users.api.views import UserViewSet
from democrasite.users.api.views import logout
from democrasite.webiscite.api.views import BillViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("bills", BillViewSet)

# Unfortunately if we want automatic links for models we can't use a namespace
# but I may reconsider anyway
# app_name = "api"  # noqa: ERA001
urlpatterns = [
    *router.urls,
    path("auth/github/", GitHubLogin.as_view(), name="github_login"),
    path("auth/logout/", logout, name="rest_logout"),
    path("token/refresh/", token_refresh, name="token_refresh"),
]
