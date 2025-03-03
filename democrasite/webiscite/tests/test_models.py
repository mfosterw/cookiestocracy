import pytest
from django.conf import settings
from django.db import IntegrityError
from factory.faker import faker

from democrasite.users.models import User
from democrasite.users.tests.factories import UserFactory
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import PullRequest
from democrasite.webiscite.models import Vote

from .factories import BillFactory
from .factories import GithubPullRequestFactory
from .factories import PullRequestFactory

# Used to generate random data inline
FAKE = faker.Faker()


class TestVote:
    def test_vote_str(self, bill: Bill, user: User):
        bill.vote(user, support=True)
        assert str(Vote.objects.get(user=user, support=True)) == f"{user} for {bill}"


class TestPullRequestManager:
    def test_create_from_github_create(self, caplog):
        pr = GithubPullRequestFactory.create(number=FAKE.random_int())
        pull_request = PullRequest.objects.create_from_github(pr)
        assert any(
            record.message == f"PR {pull_request.number}: Pull request created"
            for record in caplog.records
        )

    def test_create_from_github_update(self, bill: Bill, caplog):
        # PullRequest is created in the BillFactory
        pr = GithubPullRequestFactory.create(bill=bill)
        pull_request = PullRequest.objects.create_from_github(pr)
        assert any(
            record.message == f"PR {pull_request.number}: Pull request updated"
            for record in caplog.records
        )


class TestPullRequest:
    def test_close(self, bill: Bill):
        pull_request = bill.pull_request

        pull_request.close()

        pull_request.refresh_from_db()
        assert pull_request.status == "closed"
        assert not pull_request.bill_set.filter(status=Bill.Status.OPEN).exists()

    def test_close_no_bill(self, caplog):
        pull_request = PullRequestFactory.create()
        assert pull_request.status == "open"

        pull_request.close()

        pull_request.refresh_from_db()
        assert pull_request.status == "closed"
        assert any(
            record.message == f"PR {pull_request.number}: No open bill found"
            for record in caplog.records
        )


class TestBillManager:
    def test_create_from_github(self, user: User):
        pr = PullRequestFactory.create()
        bill = Bill.objects.create_from_github(
            pr.title,
            FAKE.text(),
            user,
            FAKE.text(),
            pr,
        )

        assert bill.pk is not None
        assert bill._submit_task.enabled is True  # noqa: SLF001


class TestBill:
    def test_unique_open_pull_request(self, bill: Bill):
        bill.status = "closed"
        bill.save()

        BillFactory.create(pull_request=bill.pull_request)

        with pytest.raises(IntegrityError, match='"unique_open_pull_request"'):
            BillFactory.create(pull_request=bill.pull_request)

    def test_bill_str(self):
        bill = BillFactory.create(name="The Test Act", pk=1, pull_request__number="-2")
        assert str(bill) == "Bill 1: The Test Act (PR #-2)"

    def test_bill_get_absolute_url(self, bill: Bill):
        assert bill.get_absolute_url() == f"/bills/{bill.id}/"

    def test_close(self, bill: Bill):
        assert bill._submit_task.enabled is True  # noqa: SLF001

        bill.close()

        bill.refresh_from_db()
        assert bill.status == Bill.Status.CLOSED
        assert bill._submit_task.enabled is False  # noqa: SLF001


class TestBillVote:
    def test_bill_vote_yes_toggle(self, bill: Bill, user: User):
        bill.vote(user, support=True)
        assert bill.yes_votes.filter(pk=user.id).exists()
        bill.vote(user, support=True)
        assert not bill.yes_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_toggle(self, bill: Bill, user: User):
        bill.vote(user, support=False)
        assert bill.no_votes.filter(pk=user.id).exists()
        bill.vote(user, support=False)
        assert not bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_yes_to_no_switch(self, bill: Bill, user: User):
        bill.vote(user, support=True)
        bill.vote(user, support=False)
        assert not bill.yes_votes.filter(pk=user.id).exists()
        assert bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_to_yes_switch(self, bill: Bill, user: User):
        bill.vote(user, support=False)
        bill.vote(user, support=True)
        assert not bill.no_votes.filter(pk=user.id).exists()
        assert bill.yes_votes.filter(pk=user.id).exists()


class TestBillSubmit:
    def test_bill_not_open(self):
        bill: Bill = BillFactory.create(status=Bill.Status.CLOSED)

        bill.submit()

        assert bill.status == Bill.Status.CLOSED

    def test_insufficient_votes(self, bill: Bill):
        bill.submit()

        assert bill.status == Bill.Status.FAILED

    def test_bill_rejected(self, bill: Bill):
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=False) for voter in voters]
        )

        bill.submit()

        assert bill.status == Bill.Status.REJECTED

    def test_constitutional_bill_rejected(self):
        bill = BillFactory.create(constitutional=True)
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=False) for voter in voters]
        )

        bill.submit()

        assert bill.status == Bill.Status.REJECTED

    def test_bill_passed(self, bill: Bill):
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=True) for voter in voters]
        )

        bill.submit()

        assert bill.status == Bill.Status.APPROVED
