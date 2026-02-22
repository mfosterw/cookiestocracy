from typing import Any

import factory

from democrasite.users.tests.factories import UserFactory
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import PullRequest


class PullRequestFactory(factory.django.DjangoModelFactory[PullRequest]):
    number = factory.Sequence(
        lambda n: -n - 1
    )  # Use negative numbers to represent fake PRs, starting at -1
    title = factory.Faker("text", max_nb_chars=50)
    author_name = factory.Faker("user_name")
    status = "open"
    draft = False
    additions = factory.Faker("random_int")
    deletions = factory.Faker("random_int")
    sha = factory.Faker("pystr", min_chars=40, max_chars=40)

    class Meta:
        model = PullRequest


class BillFactory(factory.django.DjangoModelFactory[Bill]):
    name = factory.Faker("text", max_nb_chars=50)
    description = factory.Faker("paragraph")
    author = factory.SubFactory(UserFactory)
    pull_request = factory.SubFactory(PullRequestFactory)
    # Fields with defaults
    status = Bill.Status.OPEN
    constitutional = False
    # _submit_task is created by Bill.save() for non-draft bills

    class Meta:
        model = Bill


class GithubPullRequestFactory(factory.Factory[dict[str, Any]]):
    """Generate a dict representing a pull request from the GitHub API"""

    bill = factory.SubFactory(BillFactory, status=Bill.Status.CLOSED)

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
    draft = False
    diff_url = ""  # Keep blank so request.get raises an error

    class Meta:
        model = dict
        exclude = ("bill",)
