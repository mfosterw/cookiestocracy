"""Module for all Form Tests."""

from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from democrasite.users import forms
from democrasite.users.models import User


class TestUserCreationForm:
    """
    Test class for all tests related to the UserCreationForm
    """

    def test_username_validation_error_msg(self, user: User):
        """
        Tests UserCreation Form's unique validator functions correctly by testing:
            1) A new user with an existing username cannot be added.
            2) Only 1 error is raised by the UserCreation Form
            3) The desired error message is raised
        """

        # The user already exists,
        # hence cannot be created.
        form = forms.UserAdminCreationForm(
            {
                "username": user.username,
                "password1": user.password,
                "password2": user.password,
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "username" in form.errors
        assert form.errors["username"][0] == _("This username has already been taken.")


class TestDisabledForms:
    def test_change_password_form(self, user: User):
        password = get_random_string(20)
        form = forms.DisabledChangePasswordForm(
            data={
                "oldpassword": user.password,
                "password1": password,
                "password2": password,
            },
            user=user,
        )

        assert not form.is_valid()
        assert form.errors["__all__"][0] == _("You cannot change your password.")

    def test_set_password_form(self, user: User):
        password = get_random_string(20)
        form = forms.DisabledSetPasswordForm(
            data={"password1": password, "password2": password},
            user=user,
        )

        assert not form.is_valid()
        assert form.errors["__all__"][0] == _("You cannot set a password.")

    def test_reset_password_form(self, user: User):
        form = forms.DisabledResetPasswordForm(data={"email": user.email})

        assert not form.is_valid()
        assert form.errors["__all__"][0] == _("You cannot reset your password.")

    def test_reset_key_password_form(self, user: User):
        password = get_random_string(20)
        form = forms.DisabledResetPasswordKeyForm(
            data={"password1": password, "password2": password},
            user=user,
        )

        assert not form.is_valid()
        assert form.errors["__all__"][0] == _("You cannot reset your password.")
