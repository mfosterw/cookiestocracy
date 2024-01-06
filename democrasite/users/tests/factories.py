from typing import Any, Sequence

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from factory import Faker, post_generation
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(
        obj: AbstractBaseUser, create: bool, extracted: Sequence[Any], **kwargs
    ):  # pylint: disable=unused-argument
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        obj.set_password(password)
        obj.save()

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]
        skip_postgeneration_save = True
