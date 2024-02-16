# pylint: disable=too-few-public-methods,no-self-use
from typing import Any

from ..models import Bill
from .factories import BillFactory


class TestBill:
    """Test class for all tests related to the Bill model"""

    def test_bill_str(self):
        # Gotta get that 💯% coverage. If your IDE/editor doesn't support unicode, get a better one
        bill = BillFactory(name="The Test Act", pk=1, pull_request__pr_num="-2")
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
