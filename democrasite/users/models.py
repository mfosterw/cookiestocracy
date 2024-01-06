"""Models related to users and accounts.

Starting a new project, it's highly recommended to set up a custom user model,
even if the default User model is sufficient.

This model behaves identically to the default user model, but it can be
customized in the future if the need arises.

Additional fields can be added to the model in other apps by creating a new
model with a OneToOneField to the User model.
"""

from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Default user for Democrasite."""

    name = CharField(_("Name of User"), blank=True, max_length=255)
    #: :meta private:
    first_name = None  # type: ignore
    #: :meta private:
    last_name = None  # type: ignore

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
