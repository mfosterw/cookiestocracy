"""Override forms from allauth."""

from allauth.account.forms import ChangePasswordForm
from allauth.account.forms import ResetPasswordForm
from allauth.account.forms import ResetPasswordKeyForm
from allauth.account.forms import SetPasswordForm
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserAdminChangeForm(admin_forms.UserChangeForm):
    """Override UserChangeForm to use custom User model."""

    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(admin_forms.UserCreationForm):
    """Override UserCreationForm to use custom User model."""

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User

        error_messages = {
            "username": {"unique": _("This username has already been taken.")}
        }


class DisabledChangePasswordForm(ChangePasswordForm):
    """Substitute form to disable password changes."""

    def clean(self):
        """Always raise a validation error."""
        raise ValidationError(_("You cannot change your password."))


class DisabledSetPasswordForm(SetPasswordForm):
    """Substitute form to disable password set."""

    def clean(self):
        """Always raise a validation error."""
        raise ValidationError(_("You cannot set a password."))


class DisabledResetPasswordForm(ResetPasswordForm):
    """Substitute form to disable password reset."""

    def clean(self):
        """Always raise a validation error."""
        raise ValidationError(_("You cannot reset your password."))


class DisabledResetPasswordKeyForm(ResetPasswordKeyForm):
    """Substitute form to disable password reset."""

    def clean(self):
        """Always raise a validation error."""
        raise ValidationError(_("You cannot reset your password."))
