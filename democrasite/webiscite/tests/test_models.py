# pylint: disable=too-few-public-methods,no-self-use
from typing import Any

from ..models import Bill
from .factories import BillFactory


class TestBill:
    """Test class for all tests related to the Bill model"""

    def test_bill_str(self):
        # Gotta get that 💯% coverage. If your IDE/editor doesn't support unicode, get a
        # better one
        bill = BillFactory(name="The Test Act", pr_num="-2")
        assert str(bill) == "The Test Act (PR #-2)"

    def test_bill_get_absolute_url(self, bill: Bill):
        assert bill.get_absolute_url() == f"/bills/{bill.id}/"

    def test_bill_vote_yes_toggle(self, user: Any):
        bill = BillFactory(state=Bill.OPEN)
        bill.vote(True, user)
        assert bill.yes_votes.filter(pk=user.id).exists()
        bill.vote(True, user)
        assert not bill.yes_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_toggle(self, user: Any):
        bill = BillFactory(state=Bill.OPEN)
        bill.vote(False, user)
        assert bill.no_votes.filter(pk=user.id).exists()
        bill.vote(False, user)
        assert not bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_yes_to_no_switch(self, user: Any):
        bill = BillFactory(state=Bill.OPEN)
        bill.vote(True, user)
        bill.vote(False, user)
        assert not bill.yes_votes.filter(pk=user.id).exists()
        assert bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_to_yes_switch(self, user: Any):
        bill = BillFactory(state=Bill.OPEN)
        bill.vote(False, user)
        bill.vote(True, user)
        assert not bill.no_votes.filter(pk=user.id).exists()
        assert bill.yes_votes.filter(pk=user.id).exists()
