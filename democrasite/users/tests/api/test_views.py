import pytest
from rest_framework.test import APIRequestFactory

from democrasite.users.api.views import UserViewSet
from democrasite.users.models import User


class TestUserViewSet:
    @pytest.fixture
    def view(self) -> UserViewSet:
        return UserViewSet()

    def test_get_queryset(
        self, api_rf: APIRequestFactory, user: User, view: UserViewSet
    ):
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert user in view.get_queryset()

    def test_me(self, api_rf: APIRequestFactory, user: User, view: UserViewSet):
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        response = view.me(request)  # type: ignore[call-arg,arg-type,misc]

        assert response.data == {
            "username": user.username,
            "url": f"http://testserver/api/users/{user.username}/",
            "name": user.name,
        }
