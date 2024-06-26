from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.serializers import JWTSerializer
from dj_rest_auth.views import LogoutView
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from democrasite.users.models import User

from .serializers import UserSerializer


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


# dj-rest-auth views


@extend_schema_view(
    post=extend_schema(
        summary="Login with GitHub",
        description="Login with GitHub using OAuth2",
        responses=JWTSerializer,
    )
)
class GitHubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = "http://localhost:3000/api/auth/callback/github"
    client_class = OAuth2Client


@extend_schema_view(
    get=extend_schema(exclude=True),
    post=extend_schema(
        summary="Logout",
        description="Logs out the current user and blacklists their refresh token",
        request=TokenRefreshSerializer,
    ),
)
class JwtLogoutView(LogoutView):
    pass


logout = JwtLogoutView.as_view()
