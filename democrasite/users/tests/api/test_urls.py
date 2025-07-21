from django.urls import resolve
from django.urls import reverse

from democrasite.users.models import User


def test_user_detail(user: User):
    assert (
        reverse("user-detail", kwargs={"username": user.username})
        == f"/api/users/{user.username}/"
    )
    assert resolve(f"/api/users/{user.username}/").view_name == "user-detail"


def test_user_list():
    assert reverse("user-list") == "/api/users/"
    assert resolve("/api/users/").view_name == "user-list"


def test_user_me():
    assert reverse("user-me") == "/api/users/me/"
    assert resolve("/api/users/me/").view_name == "user-me"
