# pylint: disable=too-few-public-methods,no-self-use
from typing import Any
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.forms import ValidationError
from django_celery_beat.models import PeriodicTask
from factory import Faker

from ..models import Bill, PullRequest
from .factories import BillFactory, GithubPullRequestFactory


class TestPullRequest:
    """Test class for all tests related to the PullRequest model"""

    def test_create_from_pr_create(self, caplog):
        pr = GithubPullRequestFactory(number=Faker("random_int"))
        pull_request = PullRequest.create_from_pr(pr)
        assert any(record.message == f"PR {pull_request.number}: Pull request created" for record in caplog.records)

    def test_create_from_pr_update(self, bill: Bill, caplog):
        # PullRequest is created in the BillFactory
        pr = GithubPullRequestFactory(bill=bill)
        pull_request = PullRequest.create_from_pr(pr)
        assert any(record.message == f"PR {pull_request.number}: Pull request updated" for record in caplog.records)

    def test_close(self, bill: Bill):
        bill._schedule_submit()  # pylint: disable=protected-access  # Create the submit task to be disabled
        pull_request = bill.pull_request

        pull_request.close()

        pull_request.refresh_from_db()
        assert pull_request.state == "closed"
        assert not pull_request.bill_set.filter(state=Bill.States.OPEN).exists()


class TestBill:
    """Test class for all tests related to the Bill model"""

    def test_bill_str(self):
        # Gotta get that 💯% coverage. If your IDE/editor doesn't support unicode, get a better one
        bill = BillFactory(name="The Test Act", pk=1, pull_request__number="-2")
        assert str(bill) == "Bill 1: The Test Act (PR #-2)"

    def test_bill_get_absolute_url(self, bill: Bill):
        assert bill.get_absolute_url() == f"/bills/{bill.id}/"

    def test_bill_vote_yes_toggle(self, bill: Bill, user: Any):
        bill.vote(user, True)
        assert bill.yes_votes.filter(pk=user.id).exists()
        bill.vote(user, True)
        assert not bill.yes_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_toggle(self, bill: Bill, user: Any):
        bill.vote(user, False)
        assert bill.no_votes.filter(pk=user.id).exists()
        bill.vote(user, False)
        assert not bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_yes_to_no_switch(self, bill: Bill, user: Any):
        bill.vote(user, True)
        bill.vote(user, False)
        assert not bill.yes_votes.filter(pk=user.id).exists()
        assert bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_to_yes_switch(self, bill: Bill, user: Any):
        bill.vote(user, False)
        bill.vote(user, True)
        assert not bill.no_votes.filter(pk=user.id).exists()
        assert bill.yes_votes.filter(pk=user.id).exists()

    def test_pr_opened_no_user(self):
        # If the creation step was reached, a ValidationError would be raised
        # The factory generates a random number as the user pk so it won't be found by default
        pr = GithubPullRequestFactory()

        response = Bill.create_from_pr(pr)

        assert isinstance(response[0], PullRequest)
        assert response[1] is None

    @patch("requests.get")
    def test_pr_opened_bill_exists(self, mock_get, bill: Bill):  # pylint: disable=unused-argument
        github_account = SocialAccount.objects.create(user=bill.author, provider="github", uid=Faker("random_int"))
        # The factory seems to be ignoring my arguments for some reason
        pr = GithubPullRequestFactory(bill=bill, user__id=github_account.uid)
        pr["user"]["id"] = github_account.uid

        with pytest.raises(ValidationError, match="A Bill for this pull request is already open"):
            Bill.create_from_pr(pr)

    @patch("requests.get")
    def test_opened(self, mock_get, bill: Bill):
        github_account = SocialAccount.objects.create(user=bill.author, provider="github", uid=Faker("random_int"))
        pr = GithubPullRequestFactory(bill=bill, user__id=github_account.uid)
        pr["user"]["id"] = github_account.uid
        bill.state = Bill.States.CLOSED
        bill.save()

        _, new_bill = Bill.create_from_pr(pr)

        mock_get.assert_called_once_with(pr["diff_url"], timeout=10)
        assert new_bill is not None
        assert new_bill.pull_request.number == pr["number"]
        assert new_bill.author == SocialAccount.objects.get(uid=pr["user"]["id"]).user
        assert new_bill.constitutional is False

        assert PeriodicTask.objects.filter(name=f"bill_submit:{new_bill.id}").exists()
        assert PeriodicTask.objects.get(name=f"bill_submit:{new_bill.id}").enabled is True

    def test_close(self, bill: Bill):
        task = bill._schedule_submit()  # pylint: disable=protected-access  # Create the submit task

        bill.close()

        bill.refresh_from_db()
        assert bill.state == Bill.States.CLOSED
        assert PeriodicTask.objects.get(name=task.name).enabled is False
