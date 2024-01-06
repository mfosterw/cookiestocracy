import random

from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialAccount
from factory import Faker, LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory

from democrasite.users.tests.factories import UserFactory
from democrasite.webiscite.models import Bill


class BillFactory(DjangoModelFactory):
    name = Faker("text", max_nb_chars=50)
    description = Faker("paragraph")
    pr_num = Sequence(lambda n: -n)  # Use negative numbers to represent fake PRs
    author = SubFactory(UserFactory)
    additions = Faker("random_int")
    deletions = Faker("random_int")
    sha = Faker("pystr", min_chars=40, max_chars=40)
    state = LazyFunction(lambda: random.choice(Bill.STATES)[0])
    constitutional = Faker("pybool")
    # Currently yes_votes and no_votes are initialized as empty. If values are needed
    # for them, a post-generation hook can be written to generate and insert the users

    class Meta:
        model = Bill


class SocialAccountFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    provider = LazyFunction(
        lambda: random.choice(providers.registry.get_class_list()).id
    )
    uid = Faker("random_int")

    class Meta:
        model = SocialAccount
