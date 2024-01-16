# pylint: disable=too-few-public-methods,no-self-use
from importlib import reload

import pytest
from django.contrib.admin.sites import AlreadyRegistered
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from democrasite.users.models import User


class TestUserAdmin:
    @pytest.fixture(autouse=True)
    def enable_admin(self, settings):
        # Admin site is only enabled during development
        settings.DEBUG = True

    @pytest.fixture
    def force_allauth(self, settings):
        settings.DJANGO_ADMIN_FORCE_ALLAUTH = True
        # Reload the admin module to apply the setting change
        import democrasite.users.admin as users_admin  # pylint: disable=import-outside-toplevel

        try:
            reload(users_admin)
        except AlreadyRegistered:
            pass

    @pytest.mark.usefixtures("force_allauth")
    def test_allauth_login(self, client: Client, settings):
        url = reverse("admin:login")
        response = client.get(url)

        expected_url = reverse(settings.LOGIN_URL) + "?next=" + url
        assertRedirects(response, expected_url, status_code=302, target_status_code=200)

    def test_changelist(self, admin_client: Client):
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_search(self, admin_client: Client):
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == 200

    def test_add(self, admin_client: Client):
        url = reverse("admin:users_user_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        response = admin_client.post(
            url,
            data={
                "username": "test",
                "password1": "My_R@ndom-P@ssw0rd",
                "password2": "My_R@ndom-P@ssw0rd",
            },
        )
        assert response.status_code == 302
        assert User.objects.filter(username="test").exists()

    def test_view_user(self, admin_client: Client):
        user = User.objects.get(username="admin")
        url = reverse("admin:users_user_change", kwargs={"object_id": user.pk})
        response = admin_client.get(url)
        assert response.status_code == 200
