from http import HTTPStatus

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from factory.faker import faker

from democrasite.users.forms import UserAdminChangeForm
from democrasite.users.models import User
from democrasite.users.tests.factories import UserFactory
from democrasite.users.views import UserRedirectView
from democrasite.users.views import UserUpdateView
from democrasite.users.views import user_detail_view


class TestUserUpdateView:
    def test_get_success_url(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_success_url() == f"/users/{user.username}/"

    def test_get_object(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_object() == user

    def test_form_valid(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")

        # Add the session/message middleware to the request
        SessionMiddleware(lambda r: None).process_request(request)
        MessageMiddleware(lambda r: None).process_request(request)
        request.user = user

        view.request = request

        # Initialize the form
        form = UserAdminChangeForm()
        form.cleaned_data = {}
        view.form_valid(form)

        messages_sent = [m.message for m in get_messages(request)]
        assert messages_sent == ["Information successfully updated"]


class TestUserRedirectView:
    def test_get_redirect_url(self, user: User, rf: RequestFactory):
        view = UserRedirectView()
        request = rf.get("/fake-url")
        request.user = user

        view.request = request

        assert view.get_redirect_url() == f"/users/{user.username}/"


class TestUserDetailView:
    def test_not_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()

        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_authenticated(self, user: User, rf: RequestFactory):
        user2 = UserFactory.create()

        request = rf.get("/fake-url/")
        request.user = user

        response = user_detail_view(request, username=user2.username)

        assert response.status_code == HTTPStatus.OK

    def test_github_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = user
        user.socialaccount_set.add(
            SocialAccount.objects.create(
                user=user,
                provider="github",
                uid=faker.Faker().random_int(),
            )
        )

        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        assert (
            response.context_data["empty_message"]
            == "You haven't proposed any bills yet."
        )
