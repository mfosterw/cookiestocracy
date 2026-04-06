import factory
from factory.django import DjangoModelFactory

from democrasite.social.models import Note
from democrasite.social.models import Person
from democrasite.users.tests.factories import UserFactory


class PersonFactory(DjangoModelFactory[Person]):
    user = factory.SubFactory(UserFactory)
    private_key = "PRIVATE KEY"
    public_key = "PUBLIC KEY"
    bio = factory.Faker("paragraph")

    class Meta:
        model = Person


class NoteFactory(DjangoModelFactory[Note]):
    author = factory.SubFactory(PersonFactory)
    content = factory.Faker("paragraph")
    in_reply_to = None

    class Meta:
        model = Note
