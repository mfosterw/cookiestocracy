from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from democrasite.users.api.views import GitHubLogin
from democrasite.users.api.views import UserViewSet
from democrasite.webiscite.api.views import BillViewSet
from democrasite.webiscite.api.views import VoteCreateView

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("bills", BillViewSet)

# Unfortunately if we want automatic links for models we can't use a namespace
# but I may reconsider anyway
# app_name = "api"  # noqa: ERA001
urlpatterns = [
    *router.urls,
    path("vote/", VoteCreateView.as_view(), name="vote_create"),
    path("auth/github/", GitHubLogin.as_view(), name="github_login"),
]
