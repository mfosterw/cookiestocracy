# pylint: disable=too-few-public-methods,no-self-use
import pytest
from allauth.account.models import EmailAddress
from allauth.account.views import signup
from allauth.socialaccount.helpers import complete_social_login, complete_social_signup
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.test import RequestFactory
from faker import Faker

from democrasite.users.adapters import SocialAccountAdapter
from democrasite.users.models import User
from democrasite.users.tests.factories import UserFactory


class TestAccountAdapter:
    def test_register(self, settings, rf: RequestFactory):
        """Ensure users can't sign up with registration disabled"""
        settings.ACCOUNT_ALLOW_LOCAL_REGISTRATION = False
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()

        response = signup(request)

        assert "signup_closed" in response.template_name
        assert User.objects.count() == 0


class TestSocialAccountAdapter:
    # In order to gain a better undestanding of the django-allauth system and ensure
    # everything behaved as expected in a realistic environment, I tested the
    # pre_social_login automatic linking using complete_social_login rather than calling
    # it directly
    def dummy_get_response(self, request: HttpRequest):
        return None

    @pytest.mark.xfail()
    def test_register(self, rf: RequestFactory):
        """Test that users can register automatically with a social account"""
        # In order to reduce the manual setup, this test might be better implemented
        # by mocking request.get (called to get the github api endpoint) and calling
        # GithubOauth2Provider.complete_login (see
        # https://github.com/pennersr/django-allauth/blob/master/allauth/socialaccount/providers/github/views.py
        # for aruments and more information)

        request = rf.get("/fake-url/")
        request.user = AnonymousUser()
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)

        # Create a user but do not save them to the database yet
        user = User(email=Faker().email())
        email = EmailAddress(user=user, email=user.email)
        assert user.pk is None  # not saved yet

        account = SocialAccount(provider="github", uid="1")
        sociallogin = SocialLogin(user=user, account=account, email_addresses=[email])
        complete_social_login(request, sociallogin)

        # Assert that the user and their social account exist
        assert user.pk is not None
        assert user.socialaccount_set.filter(provider=account.provider).exists()
        assert EmailAddress.objects.get(user=user).verified is False

    @pytest.mark.xfail()
    def test_connect(self, rf: RequestFactory):
        """Test that social accounts are automatically linked by email"""
        request = rf.get("/fake-url/")
        # Add the session/message middleware to the request
        request.user = AnonymousUser()
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)

        # Use .build() to avoid saving the user to the database which breaks complete_social_login
        user = UserFactory.build()
        user_email = EmailAddress(user=user, email=user.email)
        account = SocialAccount(provider="github", uid="1")
        sociallogin = SocialLogin(
            user=user, account=account, email_addresses=[user_email]
        )
        complete_social_login(request, sociallogin)

        assert user.socialaccount_set.filter(provider=account.provider).exists()  # type: ignore[attr-defined]

    @pytest.mark.xfail()
    def test_login(self, user: User, rf: RequestFactory):
        """Test that users can still login through social accounts"""
        # Use .build() to avoid saving the user to the database which breaks complete_social_login
        # user = UserFactory.build()
        user_email = EmailAddress(
            user=user, email=user.email, verified=True, primary=True
        )
        user_email.save()

        signup_request = rf.get("/fake-url/")
        signup_request.user = AnonymousUser()
        SessionMiddleware(self.dummy_get_response).process_request(signup_request)
        MessageMiddleware(self.dummy_get_response).process_request(signup_request)

        # Create an unitialized account and then manually call complete_social_login
        # This should connect the user to the provider
        signup_account = SocialAccount(provider="github", uid="1")
        signup_sociallogin = SocialLogin(
            user=user, account=signup_account, email_addresses=[user_email]
        )
        complete_social_signup(signup_request, signup_sociallogin)

        # Create a new request for the login process
        login_request = rf.get("/fake-url/")
        login_request.user = AnonymousUser()
        SessionMiddleware(self.dummy_get_response).process_request(login_request)
        MessageMiddleware(self.dummy_get_response).process_request(login_request)

        # Login again with the same account
        login_account = SocialAccount(user=user, provider="github", uid="1")
        login_sociallogin = SocialLogin(user=user, account=login_account)
        complete_social_login(login_request, login_sociallogin)

        assert login_sociallogin.is_existing
        assert login_request.user == user

    def test_disconnect(self):
        """Ensure that users cannot disconnect social accounts"""
        with pytest.raises(ValidationError):
            SocialAccountAdapter().validate_disconnect(None, None)
