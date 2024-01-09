# pylint: disable=too-few-public-methods,no-self-use
from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse

from democrasite.users.models import User


class TestUserAdmin:
    @override_settings(DJANGO_ADMIN_FORCE_ALLAUTH=True)
    def test_allauth_login(self, admin_client: Client):
        # Client starts logged in for some reason
        admin_client.logout()
        url = reverse("admin:login")
        response = admin_client.get(url, follow=True)
        print(response.request)
        print(response.content)
        print(settings.DJANGO_ADMIN_FORCE_ALLAUTH)
        assert response.request["PATH_INFO"] == reverse(settings.LOGIN_URL)
        assert False

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
