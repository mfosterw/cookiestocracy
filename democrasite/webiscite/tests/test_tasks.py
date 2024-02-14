# pylint: disable=too-few-public-methods,no-self-use
from unittest.mock import patch

import pytest
from django.conf import settings

from democrasite.users.tests.factories import UserFactory

from .. import constitution
from ..models import Bill
from ..tasks import process_pull, submit_bill
from .factories import BillFactory, SocialAccountFactory


class TestProcessPull:
    def test_pr_opened_bill_exists(self, bill: Bill):
        pr = {"number": bill.pr_num}

        with pytest.raises(ValueError):
            process_pull("reopened", pr)

    def test_pr_opened_no_user(self):
        bill = BillFactory(state=Bill.States.CLOSED)
        pr = {"number": bill.pr_num, "user": {"id": -1}}

        process_pull("reopened", pr)

        assert Bill.objects.filter(name=bill.name).count() == 1

    @patch.object(submit_bill, "apply_async")
    @patch("requests.get")
    def test_pr_opened(self, mock_get, mock_submit):
        bill = BillFactory(state=Bill.States.CLOSED)
        # Create user account using SocialAccountFactory to mock linked github
        github_account = SocialAccountFactory(provider="github")
        mock_get().text = ""  # diff text
        # Use a mocked bill object to provide realistic values for PR
        pr = {
            "user": {
                "id": github_account.uid,
            },
            "head": {
                "sha": bill.sha,
            },
            "title": bill.name,
            "body": bill.description,
            "number": bill.pr_num,
            "additions": bill.additions,
            "deletions": bill.deletions,
            "diff_url": "example.com",
        }

        process_pull("reopened", pr)

        new_bill = Bill.objects.get(name=bill.name, state=Bill.States.OPEN)
        assert new_bill.pr_num == bill.pr_num
        assert new_bill.author == github_account.user
        assert new_bill.constitutional is False

        assert mock_submit.call_args[0][0][0] == new_bill.id

    def test_pr_closed_bill_not_open(self):
        bill = BillFactory(state=Bill.States.FAILED)
        pr = {"number": bill.pr_num}

        process_pull("closed", pr)

        bill.refresh_from_db()
        assert bill.state == Bill.States.FAILED

    def test_pr_closed(self, bill: Bill):
        pr = {"number": bill.pr_num}

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
        for voter in voters:
            bill.vote(False, voter)

        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.REJECTED
        mock_repo().get_pull().edit.assert_called_once_with(state="closed")

    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_constitutional_bill_rejected(self, mock_token, mock_repo):  # pylint: disable=unused-argument
        bill = BillFactory(state=Bill.States.OPEN, constitutional=True)
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        for voter in voters:
            bill.vote(False, voter)

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
        for voter in voters:
            bill.vote(True, voter)

        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.APPROVED
        mock_repo().get_pull().merge.assert_called_once_with(merge_method="squash", sha=bill.sha)
        mock_repo().get_contents.assert_called_once_with("democrasite/webiscite/constitution.json")
