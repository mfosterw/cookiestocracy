"""This module contains adapters for the allauth package.

The adapters are used to customize the behavior of allauth accounts. These are
used to allow disabling local and social account registration via settings.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest

User = get_user_model()


class AccountAdapter(DefaultAccountAdapter):
    """Adapter for accounts, overwritten to allow disabling local account
    registration with a setting"""

    def is_open_for_signup(self, request: HttpRequest):
        return getattr(settings, "ACCOUNT_ALLOW_LOCAL_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Adapter for social accounts, overwritten to allow disabling social
    account registration with a setting"""

    def is_open_for_signup(self, request: HttpRequest, sociallogin: SocialLogin) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    # TODO: Allow requiring verification for each social account via setting
