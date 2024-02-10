"""Users app configuration."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    """Users app definition."""

    name = "democrasite.users"
    verbose_name = _("Users")
