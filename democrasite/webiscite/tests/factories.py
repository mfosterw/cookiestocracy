from factory import Faker, Sequence, SubFactory
from factory.django import DjangoModelFactory

from democrasite.users.tests.factories import UserFactory
from democrasite.webiscite.models import Bill, PullRequest


class PullRequestFactory(DjangoModelFactory):
    pr_num = Sequence(lambda n: -n)  # Use negative numbers to represent fake PRs
    title = Faker("text", max_nb_chars=50)
    author_name = Faker("user_name")
    state = Faker("random_element", elements=["open", "closed"])
    additions = Faker("random_int")
    deletions = Faker("random_int")
    sha = Faker("pystr", min_chars=40, max_chars=40)

    class Meta:
        model = PullRequest


class BillFactory(DjangoModelFactory):
    name = Faker("text", max_nb_chars=50)
    description = Faker("paragraph")
    author = SubFactory(UserFactory)
    pull_request = SubFactory(PullRequestFactory)
    # Fields with defaults
    state = Bill.States.OPEN
    constitutional = False
    # Currently yes_votes and no_votes are initialized as empty. If values are needed
    # for them, a post-generation hook can be written to generate and insert the users

    class Meta:
        model = Bill
