from unittest.mock import patch

from django.conf import settings

from democrasite.users.tests.factories import UserFactory
from democrasite.webiscite import constitution
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import Vote
from democrasite.webiscite.tasks import submit_bill

from .factories import BillFactory


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
    def test_insufficient_votes(self, mock_token, mock_repo, mock_get, bill: Bill):
        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.FAILED
        mock_repo().get_pull().edit.assert_called_once_with(state="closed")

    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_bill_rejected(self, mock_token, mock_repo, bill: Bill):
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=False) for voter in voters]
        )

        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.REJECTED
        mock_repo().get_pull().edit.assert_called_once_with(state="closed")

    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_constitutional_bill_rejected(self, mock_token, mock_repo):
        bill = BillFactory(state=Bill.States.OPEN, constitutional=True)
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=False) for voter in voters]
        )

        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.REJECTED
        mock_repo().get_pull().edit.assert_called_once_with(state="closed")

    @patch.object(constitution, "update_constitution")
    @patch("requests.get")  # patch out requests.get to avoid using internet
    @patch("github.Github.get_repo")
    @patch("github.Auth.Token", spec=True)
    def test_bill_passed(  # noqa: PLR0913
        self, mock_token, mock_repo, mock_get, mock_constitution, bill: Bill
    ):
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=True) for voter in voters]
        )

        submit_bill(bill.id)

        bill.refresh_from_db()
        assert bill.state == Bill.States.APPROVED
        mock_repo().get_pull().merge.assert_called_once_with(
            merge_method="squash", sha=bill.pull_request.sha
        )
        mock_repo().get_contents.assert_called_once_with(
            "democrasite/webiscite/constitution.json"
        )
