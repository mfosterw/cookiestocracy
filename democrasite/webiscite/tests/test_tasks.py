# pylint: disable=too-few-public-methods,no-self-use
from unittest.mock import patch

import pytest
import requests
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.forms import ValidationError
from factory import Faker

from democrasite.users.tests.factories import UserFactory

from .. import constitution
from ..models import Bill, Vote
from ..tasks import process_pull, submit_bill
from .factories import BillFactory


class TestProcessPull:
    @pytest.fixture
    def pr(self, bill: Bill, monkeypatch):
        github_account = SocialAccount.objects.create(user=bill.author, provider="github", uid=Faker("random_int"))
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: requests.Response())

        return {
            "user": {
                "id": github_account.uid,
                "login": bill.author.username,
            },
            "head": {
                "sha": bill.pull_request.sha,
            },
            "title": bill.name,
            "body": bill.description,
            "number": bill.pull_request.pr_num,
            "state": "open",
            "additions": bill.pull_request.additions,
            "deletions": bill.pull_request.deletions,
            # Don't actually put something here so it errors if request.get isn't mocked
            "diff_url": "",
        }

    def test_pr_opened_bill_exists(self, pr):
        with pytest.raises(ValidationError, match="A Bill for this pull request is already open"):
            process_pull("opened", pr)

    def test_pr_opened_no_user(self, pr):
        # If the creation step was reached, a ValidationError would be raised
        pr["user"]["id"] = -1

        process_pull("reopened", pr)

        assert Bill.objects.filter(name=pr["title"]).count() == 1

    @patch.object(submit_bill, "apply_async")
    def test_pr_opened(self, mock_submit, pr):
        bill = Bill.objects.get(name=pr["title"])
        bill.state = Bill.States.CLOSED
        bill.save()

        process_pull("reopened", pr)

        new_bill = Bill.objects.get(name=bill.name, state=Bill.States.OPEN)
        assert new_bill.pull_request.pr_num == pr["number"]
        assert new_bill.author == SocialAccount.objects.get(uid=pr["user"]["id"]).user
        assert new_bill.constitutional is False

        assert mock_submit.call_args[0][0][0] == new_bill.id

    def test_pr_closed_bill_not_open(self):
        bill: Bill = BillFactory(state=Bill.States.FAILED)
        pr = {"number": bill.pull_request.pr_num}

        process_pull("closed", pr)

        bill.refresh_from_db()
        assert bill.state == Bill.States.FAILED

    def test_pr_closed(self, bill: Bill):
        pr = {"number": bill.pull_request.pr_num}

        process_pull("closed", pr)

        bill.refresh_from_db()
        assert bill.state == Bill.States.CLOSED

    def test_other_action(self):
        pr = {"number": -1}

        process_pull("other", pr)  # Basically just ensure it won't crash


class TestSubmitBill:
    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_bill_not_open(self, mock_token, mock_repo):
        bill = BillFactory(state=Bill.States.CLOSED)

        submit_bill(bill.id)

        mock_token.assert_called_once_with(settings.WEBISCITE_GITHUB_TOKEN)
        mock_repo().get_pull().edit.assert_called_once_with(state="closed")

    @patch("requests.get")
    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_insufficient_votes(self, mock_token, mock_repo, mock_get, bill: Bill):  # pylint: disable=unused-argument
        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.FAILED
        mock_repo().get_pull().edit.assert_called_once_with(state="closed")

    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_bill_rejected(self, mock_token, mock_repo, bill: Bill):  # pylint: disable=unused-argument
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create([Vote(bill=bill, user=voter, support=False) for voter in voters])

        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.REJECTED
        mock_repo().get_pull().edit.assert_called_once_with(state="closed")

    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_constitutional_bill_rejected(self, mock_token, mock_repo):  # pylint: disable=unused-argument
        bill = BillFactory(state=Bill.States.OPEN, constitutional=True)
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create([Vote(bill=bill, user=voter, support=False) for voter in voters])

        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.REJECTED
        mock_repo().get_pull().edit.assert_called_once_with(state="closed")

    @patch.object(constitution, "update_constitution")
    @patch("requests.get")  # patch out requests.get to avoid using internet
    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_bill_passed(
        self, mock_token, mock_repo, mock_get, mock_constitution, bill: Bill
    ):  # pylint: disable=unused-argument
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create([Vote(bill=bill, user=voter, support=True) for voter in voters])

        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.APPROVED
        mock_repo().get_pull().merge.assert_called_once_with(merge_method="squash", sha=bill.pull_request.sha)
        mock_repo().get_contents.assert_called_once_with("democrasite/webiscite/constitution.json")
