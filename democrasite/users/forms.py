from allauth.account.forms import (
    ChangePasswordForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
    SetPasswordForm,
)
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserChangeForm(auth_forms.UserChangeForm):
    class Meta(auth_forms.UserChangeForm.Meta):
        model = User


class UserCreationForm(auth_forms.UserCreationForm):
    class Meta(auth_forms.UserCreationForm.Meta):
        model = User

        error_messages = {
            "username": {"unique": _("This username has already been taken.")}
        }


class DisabledChangePasswordForm(ChangePasswordForm):
    def clean(self):
        raise ValidationError(_("You cannot change your password."))


class DisabledSetPasswordForm(SetPasswordForm):
    def clean(self):
        raise ValidationError(_("You cannot set a password."))


class DisabledResetPasswordForm(ResetPasswordForm):
    def clean(self):
        raise ValidationError(_("You cannot reset your password."))


class DisabledResetPasswordKeyForm(ResetPasswordKeyForm):
    def clean(self):
        raise ValidationError(_("You cannot reset your password."))
