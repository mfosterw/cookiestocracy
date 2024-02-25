from factory import Faker
from factory import post_generation
from factory.django import DjangoModelFactory

from democrasite.users.models import User


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(obj: User, create: bool, extracted: str, **kwargs):  # noqa: N805, FBT001
        password = extracted or Faker(
            "password",
            length=42,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True,
        ).evaluate(None, None, extra={"locale": None})
        obj.set_password(password)
        obj.save()

    class Meta:
        model = User
        django_get_or_create = ["username"]
        skip_postgeneration_save = True
