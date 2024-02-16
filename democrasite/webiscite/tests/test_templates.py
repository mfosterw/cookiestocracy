"""Render each branch on each template to ensure there are no rendering errors."""

# pylint: disable=too-few-public-methods,no-self-use
import pytest
from django.test import Client
from django.urls import reverse
from django.utils.html import escape

from ..models import Bill
from .factories import BillFactory


class TestBillDetailTemplate:
    def _test_get_response(self, client: Client, bill_id: int):
        response = client.get(reverse("webiscite:bill-detail", args=(bill_id,)))
        result = response.content.decode()

        assert response.status_code == 200
        assert response.templates[0].name == "webiscite/bill_detail.html"
        return result

    def test_logged_out(self, bill: Bill, client: Client):
        content = self._test_get_response(client, bill.id)

        assert "Log in to vote" in content
        assert "vote.js" not in content

    def test_logged_in(self, bill: Bill, client: Client):
        client.force_login(bill.author)

        content = self._test_get_response(client, bill.id)

        assert "vote.js" in content
        assert "svg" in content
        assert bill.get_state_display() not in content

    @pytest.mark.parametrize("state,constitutional", [(Bill.States.FAILED, True), (Bill.States.APPROVED, False)])
    def test_bill_closed(self, client: Client, user, state: Bill.States, constitutional: bool):
        bill = BillFactory(state=state, author=user, constitutional=constitutional)

        content = self._test_get_response(client, bill.id)

        assert "Log in to vote" not in content
        assert "vote.js" not in content
        assert "svg" not in content
        assert bill.get_state_display() in content
        assert ("Constitution" in content) == constitutional


class TestBillUpdateTemplate:
    def test_bill_form(self, bill: Bill, client: Client):
        client.force_login(bill.author)

        response = client.get(reverse("webiscite:bill-update", args=(bill.id,)))

        assert response.status_code == 200
        assert response.templates[0].name == "webiscite/bill_form.html"


class TestBillListTemplate:
    @pytest.mark.parametrize("view", ["index", "my-bills", "my-bill-votes"])
    def test_empty(self, client: Client, user, view):
        client.force_login(user)

        response = client.get(reverse(f"webiscite:{view}"))
        content = response.content.decode()

        assert response.status_code == 200
        assert response.templates[0].name == "webiscite/bill_list.html"
        assert ("No bills" in content) == (view == "index")
        assert (escape("you haven't proposed any bills") in content) == (view == "my-bills")
        assert (escape("you haven't voted on any bills") in content) == (view == "my-bill-votes")

    @pytest.mark.parametrize("constitutional", [True, False])
    def test_logged_out(self, client: Client, constitutional: bool):
        bill = BillFactory(constitutional=constitutional)

        response = client.get(reverse("webiscite:index"))
        content = response.content.decode()

        assert response.status_code == 200
        assert bill.name in content
        assert "Log in to vote" in content
        assert "vote.js" not in content
        assert ("Constitution" in content) == constitutional

    @pytest.mark.parametrize(
        "view,state",
        [
            ("index", Bill.States.OPEN),
            ("my-bills", Bill.States.APPROVED),
            ("my-bills", Bill.States.REJECTED),
            ("my-bill-votes", Bill.States.OPEN),
            ("my-bill-votes", Bill.States.FAILED),
        ],
    )
    def test_my_bills(self, state: Bill.States, view: str, bill: Bill, client: Client):
        if view == "my-bill-votes":
            bill.vote(bill.author, True)
        bill.state = state
        bill.save()

        client.force_login(bill.author)
        response = client.get(reverse(f"webiscite:{view}"))
        content = response.content.decode()

        assert response.status_code == 200
        assert bill.name in content
        assert "Log in to vote" not in content
        assert "vote.js" in content
        assert (bill.get_state_display() in content) == (bill.state != Bill.States.OPEN)
