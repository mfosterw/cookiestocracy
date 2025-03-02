from typing import Any
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.forms import ValidationError
from django_celery_beat.models import PeriodicTask
from factory import Faker

from democrasite.users.tests.factories import UserFactory
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import PullRequest
from democrasite.webiscite.models import Vote

from .factories import BillFactory
from .factories import GithubPullRequestFactory
from .factories import PullRequestFactory


class TestVote:
    """Test class for all tests related to the Vote model"""

    def test_vote_str(self, bill: Bill, user: Any):
        bill.vote(user, support=True)
        assert str(Vote.objects.get(user=user, support=True)) == f"{user} for {bill}"


class TestPullRequest:
    """Test class for all tests related to the PullRequest model"""

    def test_create_from_pr_create(self, caplog):
        pr = GithubPullRequestFactory.create(number=Faker("random_int"))
        pull_request = PullRequest.create_from_pr(pr)
        assert any(
            record.message == f"PR {pull_request.number}: Pull request created"
            for record in caplog.records
        )

    def test_create_from_pr_update(self, bill: Bill, caplog):
        # PullRequest is created in the BillFactory
        pr = GithubPullRequestFactory.create(bill=bill)
        pull_request = PullRequest.create_from_pr(pr)
        assert any(
            record.message == f"PR {pull_request.number}: Pull request updated"
            for record in caplog.records
        )

    def test_close(self, bill: Bill):
        bill._schedule_submit()  # noqa: SLF001 # Create the submit task to be disabled
        pull_request = bill.pull_request

        pull_request.close()

        pull_request.refresh_from_db()
        assert pull_request.status == "closed"
        assert not pull_request.bill_set.filter(status=Bill.Status.OPEN).exists()

    def test_close_no_bill(self):
        pull_request = PullRequestFactory.create()
        assert pull_request.status == "open"

        pull_request.close()

        pull_request.refresh_from_db()
        assert pull_request.status == "closed"
        assert not pull_request.bill_set.exists()


class TestBill:
    """Test class for all tests related to the Bill model"""

    def test_bill_str(self):
        bill = BillFactory.create(name="The Test Act", pk=1, pull_request__number="-2")
        assert str(bill) == "Bill 1: The Test Act (PR #-2)"

    def test_bill_get_absolute_url(self, bill: Bill):
        assert bill.get_absolute_url() == f"/bills/{bill.id}/"


class TestBillVote:
    def test_bill_vote_yes_toggle(self, bill: Bill, user: Any):
        bill.vote(user, support=True)
        assert bill.yes_votes.filter(pk=user.id).exists()
        bill.vote(user, support=True)
        assert not bill.yes_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_toggle(self, bill: Bill, user: Any):
        bill.vote(user, support=False)
        assert bill.no_votes.filter(pk=user.id).exists()
        bill.vote(user, support=False)
        assert not bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_yes_to_no_switch(self, bill: Bill, user: Any):
        bill.vote(user, support=True)
        bill.vote(user, support=False)
        assert not bill.yes_votes.filter(pk=user.id).exists()
        assert bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_to_yes_switch(self, bill: Bill, user: Any):
        bill.vote(user, support=False)
        bill.vote(user, support=True)
        assert not bill.no_votes.filter(pk=user.id).exists()
        assert bill.yes_votes.filter(pk=user.id).exists()


class TestBillOpened:
    def test_pr_opened_no_user(self):
        # If the creation step was reached, a ValidationError would be raised
        # The factory doesn't create a real user, so we can use it here
        pr = GithubPullRequestFactory.create()

        response = Bill.create_from_pr(pr)

        assert isinstance(response[0], PullRequest)
        assert response[1] is None

    @patch("requests.get")
    def test_pr_opened_bill_exists(self, mock_get, bill: Bill):
        github_account = SocialAccount.objects.create(
            user=bill.author, provider="github", uid=Faker("random_int")
        )
        # The factory seems to be ignoring my arguments for some reason
        pr = GithubPullRequestFactory.create(bill=bill, user__id=github_account.uid)
        pr["user"]["id"] = github_account.uid

        with pytest.raises(
            ValidationError, match="A Bill for this pull request is already open"
        ):
            Bill.create_from_pr(pr)

    @patch("requests.get")
    def test_opened(self, mock_get, bill: Bill):
        github_account = SocialAccount.objects.create(
            user=bill.author, provider="github", uid=Faker("random_int")
        )
        pr = GithubPullRequestFactory.create(bill=bill, user__id=github_account.uid)
        pr["user"]["id"] = github_account.uid
        bill.status = Bill.Status.CLOSED
        bill.save()

        _, new_bill = Bill.create_from_pr(pr)

        mock_get.assert_called_once_with(pr["diff_url"], timeout=10)
        assert new_bill is not None
        assert new_bill.pull_request.number == pr["number"]
        assert new_bill.author == SocialAccount.objects.get(uid=pr["user"]["id"]).user
        assert new_bill.constitutional is False

        assert PeriodicTask.objects.filter(name=f"bill_submit:{new_bill.id}").exists()
        assert (
            PeriodicTask.objects.get(name=f"bill_submit:{new_bill.id}").enabled is True
        )


class TestBillClosed:
    def test_close(self, bill: Bill):
        task = bill._schedule_submit()  # noqa: SLF001 # Create the submit task to be disabled

        bill.close()

        bill.refresh_from_db()
        assert bill.status == Bill.Status.CLOSED
        assert PeriodicTask.objects.get(name=task.name).enabled is False


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
