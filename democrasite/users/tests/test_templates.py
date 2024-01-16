"""Render each branch on each template to ensure there are no rendering errors."""
# pylint: disable=too-few-public-methods,no-self-use
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.shortcuts import render
from django.test import Client, RequestFactory
from django.urls import reverse
from django.views.defaults import page_not_found, permission_denied, server_error

from democrasite.users.models import User
from democrasite.users.tests.factories import UserFactory


class TestRootTemplates:
    # TODO: These should be somewhere else
    def dummy_get_response(self, request: HttpRequest):
        return None

    def test_base(self, rf: RequestFactory, user: User):
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)
        messages.info(request, "This is a test message")

        response = render(request, "base.html")

        assert response.status_code == 200
        assert b"This is a test message" in response.content
        assert b"login-dropdown" in response.content, "should be visible to logged out users"
        assert b"logout-form" not in response.content, "should not be visible to logged out users"

        request.user = user

        response = render(request, "base.html")

        assert b"login-dropdown" not in response.content, "should not be visible to logged in users"
        assert b"logout-form" in response.content, "should be visible to logged out users"

    def test_403_with_message(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = permission_denied(request, exception=Exception("Test message"))

        assert response.status_code == 403
        assert b"Test message" in response.content

    def test_403_without_message(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = permission_denied(request, exception=Exception(""))

        assert response.status_code == 403
        assert b"You're not allowed to access this page." in response.content

    def test_404_without_message(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = page_not_found(request, exception=Exception(""))

        assert response.status_code == 404
        assert b"This is not the page you were looking for." in response.content

    def test_404_with_message(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = page_not_found(request, exception=Exception("Test message"))

        assert response.status_code == 404
        assert b"Test message" in response.content

    def test_500(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = server_error(request)

        assert response.status_code == 500
        assert b"Error" in response.content

    def test_page_disabled(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = render(request, "page_disabled.html")

        assert response.status_code == 200
        assert b"Page Unavailable" in response.content


class TestPagesTemplates:
    # TODO: These should be somewhere else
    def test_about(self, client: Client):
        response = client.get(reverse("about"))

        assert response.status_code == 200
        assert response.templates[0].name == "pages/about.html"

    def test_privacy(self, client: Client):
        response = client.get(reverse("privacy"))

        assert response.status_code == 200
        assert response.templates[0].name == "pages/privacy.html"


class TestUsersTemplates:
    def test_user_detail(self, client: Client, user: User):
        visitor = UserFactory()
        client.force_login(visitor)

        response = client.get(reverse("users:detail", args=(user.username,)))

        assert response.status_code == 200
        assert response.templates[0].name == "users/user_detail.html"
        assert b"My Info" not in response.content

        client.force_login(user)

        response = client.get(reverse("users:detail", args=(user.username,)))

        assert b"My Info" in response.content

    def test_user_form(self, client: Client, user: User):
        client.force_login(user)

        response = client.get(reverse("users:update"))

        assert response.status_code == 200
        assert response.templates[0].name == "users/user_form.html"
