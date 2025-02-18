import contextlib
from http import HTTPStatus
from importlib import reload

import pytest
from django.contrib.admin.sites import AlreadyRegistered
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from democrasite.users.models import User


class TestUserAdmin:
    @pytest.fixture(autouse=True)
    def _enable_admin(self, settings):
        # Admin site is only enabled during development
        settings.DEBUG = True

    @pytest.fixture
    def _force_allauth(self, settings):
        settings.DJANGO_ADMIN_FORCE_ALLAUTH = True
        # Reload the admin module to apply the setting change
        import democrasite.users.admin as users_admin

        with contextlib.suppress(AlreadyRegistered):
            reload(users_admin)

    @pytest.mark.usefixtures("_force_allauth")
    def test_allauth_login(self, client: Client, settings):
        url = reverse("admin:login")
        response = client.get(url)

        expected_url = f"{reverse(settings.LOGIN_URL)}?next={url}"
        assertRedirects(response, expected_url, status_code=302, target_status_code=200)

    def test_changelist(self, admin_client: Client):
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_search(self, admin_client: Client):
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client: Client):
        url = reverse("admin:users_user_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        response = admin_client.post(
            url,
            data={
                "username": "test",
                "password1": "My_R@ndom-P@ssw0rd",
                "password2": "My_R@ndom-P@ssw0rd",
            },
        )
        assert response.status_code == HTTPStatus.FOUND
        assert User.objects.filter(username="test").exists()

    def test_view_user(self, admin_client: Client):
        user = User.objects.get(username="admin")
        url = reverse("admin:users_user_change", kwargs={"object_id": user.pk})
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK
