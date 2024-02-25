import factory

from democrasite.users.tests.factories import UserFactory
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import PullRequest


class PullRequestFactory(factory.django.DjangoModelFactory):
    number = factory.Sequence(
        lambda n: -n
    )  # Use negative numbers to represent fake PRs
    title = factory.Faker("text", max_nb_chars=50)
    author_name = factory.Faker("user_name")
    state = "open"
    additions = factory.Faker("random_int")
    deletions = factory.Faker("random_int")
    sha = factory.Faker("pystr", min_chars=40, max_chars=40)

    class Meta:
        model = PullRequest


class BillFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("text", max_nb_chars=50)
    description = factory.Faker("paragraph")
    author = factory.SubFactory(UserFactory)
    pull_request = factory.SubFactory(PullRequestFactory)
    # Fields with defaults
    state = Bill.States.OPEN
    constitutional = False
    # Currently yes_votes and no_votes are initialized as empty. If values are needed
    # for them, a post-generation hook can be written to generate and insert the users

    class Meta:
        model = Bill


class GithubPullRequestFactory(factory.Factory):
    bill = factory.SubFactory(BillFactory)

    user = factory.DictFactory(
        id=factory.Faker("random_int"), login=factory.Faker("user_name")
    )
    head = factory.DictFactory(sha=factory.Faker("pystr", min_chars=40, max_chars=40))
    title = factory.SelfAttribute("bill.name")
    body = factory.SelfAttribute("bill.description")
    number = factory.SelfAttribute("bill.pull_request.number")
    state = "open"
    additions = factory.SelfAttribute("bill.pull_request.additions")
    deletions = factory.SelfAttribute("bill.pull_request.deletions")
    diff_url = ""  # Keep blank so request.get raises an error

    class Meta:
        model = dict
        exclude = ("bill",)
