"""Render each branch on each template to ensure there are no rendering errors."""

from http import HTTPStatus
from importlib import reload

import pytest
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.shortcuts import render
from django.test import Client
from django.test import RequestFactory
from django.urls import clear_url_caches
from django.urls import reverse
from django.views.defaults import page_not_found
from django.views.defaults import permission_denied
from django.views.defaults import server_error

from democrasite.users.models import User
from democrasite.users.tests.factories import UserFactory


class TestRootTemplates:
    @pytest.fixture
    def _enable_admin(self, settings):
        # Admin site is only enabled during development
        settings.DEBUG = True

        from config import api_router
        from config import urls

        reload(api_router)
        reload(urls)
        clear_url_caches()

    # TODO: These should be somewhere else
    @pytest.mark.usefixtures("_enable_admin")
    def test_base(self, rf: RequestFactory, user: User):
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()
        SessionMiddleware(lambda r: None).process_request(request)  # type: ignore[arg-type]
        MessageMiddleware(lambda r: None).process_request(request)  # type: ignore[arg-type]
        messages.info(request, "This is a test message")

        response = render(request, "base.html")

        assert response.status_code == HTTPStatus.OK
        assert b"This is a test message" in response.content
        assert b"login-dropdown" in response.content, (
            "Login should be visible to logged out users"
        )
        assert b"form-inline" not in response.content, (
            "Logout should not be visible to logged out users"
        )

        request.user = user

        response = render(request, "base.html")

        assert b"login-dropdown" not in response.content, (
            "Login should not be visible to logged in users"
        )
        assert b"form-inline" in response.content, (
            "Logout should be visible to logged in users"
        )
        assert reverse("admin:index") in response.content.decode(), (
            "Admin site link should be visible when debug is on"
        )

    def test_403_with_message(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = permission_denied(request, exception=Exception("Test message"))

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert b"Test message" in response.content

    def test_403_without_message(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = permission_denied(request, exception=Exception(""))

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert b"You're not allowed to access this page." in response.content

    def test_404_without_message(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = page_not_found(request, exception=Exception(""))

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert b"This is not the page you were looking for." in response.content

    def test_404_with_message(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = page_not_found(request, exception=Exception("Test message"))

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert b"Test message" in response.content

    def test_500(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = server_error(request)

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert b"Error" in response.content

    def test_page_disabled(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        response = render(request, "page_disabled.html")

        assert response.status_code == HTTPStatus.OK
        assert b"Page Unavailable" in response.content


class TestPagesTemplates:
    # TODO: These should be somewhere else
    def test_about(self, client: Client):
        response = client.get(reverse("about"))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "pages/about.html"

    def test_privacy(self, client: Client):
        response = client.get(reverse("privacy"))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "pages/privacy.html"


class TestUsersTemplates:
    def test_user_detail(self, client: Client, user: User):
        visitor = UserFactory.create()
        client.force_login(visitor)

        response = client.get(reverse("users:detail", args=(user.username,)))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "users/user_detail.html"
        assert b"My Info" not in response.content

        client.force_login(user)

        response = client.get(reverse("users:detail", args=(user.username,)))

        assert b"My Info" in response.content

    def test_user_form(self, client: Client, user: User):
        client.force_login(user)

        response = client.get(reverse("users:update"))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "users/user_form.html"
