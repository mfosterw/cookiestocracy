from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        return getattr(settings, "ACCOUNT_ALLOW_LOCAL_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: SocialLogin):
        return getattr(settings, "ACCOUNT_ALLOW_SOCIAL_REGISTRATION", True)

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin):
        """Invoked just after a user successfully authenticates via a social provider,
        but before the login is actually processed (and before the pre_social_login
        signal is emitted).

        If a social account with an email address associated with an existing user is
        provided, they will automatically be linked if not already linked.
        """
        # social account already exists, so this is just a login
        if sociallogin.is_existing:
            return

        # NOTE: Eventually I want to rewrite the login flow to always require email
        # verification for each new social account connection.

        assert (
            sociallogin.email_addresses is not None
        ), "All logins should include an email address"

        # If user does not exist, their account should be created
        try:
            user = User.objects.get(email=sociallogin.email_addresses[0].email)
        except User.DoesNotExist:
            return

        # If user exists, connect the account to the existing account and login
        sociallogin.connect(request, user)

    def validate_disconnect(self, account, accounts):
        """
        Disables users disconnecting social accounts
        """
        raise ValidationError(
            _("Social accounts may not be disconnected at this time.")
        )
