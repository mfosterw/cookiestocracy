from unittest.mock import patch

from django.conf import settings

from democrasite.users.tests.factories import UserFactory
from democrasite.webiscite import constitution
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import Vote
from democrasite.webiscite.tasks import _update_constitution
from democrasite.webiscite.tasks import submit_bill

from .factories import BillFactory


class TestSubmitBill:
    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_bill_failed(self, mock_token, mock_repo):
        bill = BillFactory.create(status=Bill.Status.CLOSED)

        submit_bill(bill.id)

        mock_token.assert_called_once_with(settings.WEBISCITE_GITHUB_TOKEN)
        mock_repo.assert_called_once_with(settings.WEBISCITE_REPO)
        mock_repo().get_pull().edit.assert_called_once_with(state="closed")

    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_bill_passed(self, mock_token, mock_repo):
        bill = BillFactory.create(constitutional=True)
        # constitutional so _update_constitution isn't called
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=True) for voter in voters]
        )

        submit_bill(bill.id)

        mock_repo().get_pull().merge.assert_called_once_with(
            merge_method="squash", sha=bill.pull_request.sha
        )

    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_bill_merge_failed(self, mock_token, mock_repo):
        bill = BillFactory.create(constitutional=True)
        # constitutional so _update_constitution isn't called
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=True) for voter in voters]
        )
        mock_repo().get_pull().merge.return_value = None

        submit_bill(bill.id)

        mock_repo().get_pull().merge.assert_called_once_with(
            merge_method="squash", sha=bill.pull_request.sha
        )

    @patch.object(constitution, "update_constitution")
    @patch("requests.get")
    @patch("github.Repository.Repository")
    def test_update_constitution(
        self, mock_repo, mock_get, mock_constitution, bill: Bill
    ):
        _update_constitution(bill, mock_repo)

        mock_get.assert_called_once_with(bill.pull_request.diff_url, timeout=60)
        mock_constitution.assert_called_once()
        mock_repo.get_contents.assert_called_once_with(
            "democrasite/webiscite/constitution.json"
        )
        mock_repo.update_file.assert_called_once()
