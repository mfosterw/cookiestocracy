"""Render each branch on each template to ensure there are no rendering errors."""

from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse
from django.utils.html import escape

from democrasite.webiscite.models import Bill

from .factories import BillFactory


class TestBillDetailTemplate:
    def _test_get_response(self, client: Client, bill_id: int):
        response = client.get(reverse("webiscite:bill-detail", args=(bill_id,)))
        result = response.content.decode()

        assert response.status_code == HTTPStatus.OK
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
        assert reverse("webiscite:bill-update", args=(bill.id,)) in content
        assert bill.get_status_display() not in content

    @pytest.mark.parametrize(
        ("status", "constitutional"),
        [
            (Bill.Status.FAILED, True),
            (Bill.Status.APPROVED, False),
            (Bill.Status.DRAFT, False),
        ],
    )
    def test_bill_closed(
        self,
        client: Client,
        user,
        status: Bill.Status,
        constitutional: bool,  # noqa: FBT001
    ):
        bill = BillFactory.create(
            status=status, author=user, constitutional=constitutional
        )

        content = self._test_get_response(client, bill.id)

        assert "Log in to vote" not in content
        assert "vote.js" not in content
        assert "svg" not in content
        assert bill.get_status_display() in content
        assert ("Constitution" in content) == constitutional


class TestBillUpdateTemplate:
    def test_bill_form(self, bill: Bill, client: Client):
        client.force_login(bill.author)

        response = client.get(reverse("webiscite:bill-update", args=(bill.id,)))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "webiscite/bill_form.html"


class TestBillListTemplate:
    @pytest.mark.parametrize("view", ["index", "my-bills", "my-bill-votes"])
    def test_empty(self, client: Client, user, view):
        client.force_login(user)

        response = client.get(reverse(f"webiscite:{view}"))
        content = response.content.decode()

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "webiscite/bill_list.html"
        assert ("No bills" in content) == (view == "index")
        assert (escape("You haven't proposed any bills") in content) == (
            view == "my-bills"
        )
        assert (escape("You haven't voted on any bills") in content) == (
            view == "my-bill-votes"
        )

    @pytest.mark.parametrize("constitutional", [True, False])
    def test_logged_out(self, client: Client, constitutional: bool):  # noqa: FBT001
        bill = BillFactory.create(constitutional=constitutional)

        response = client.get(reverse("webiscite:index"))
        content = response.content.decode()

        assert response.status_code == HTTPStatus.OK
        assert bill.name in content
        assert "Log in to vote" in content
        assert "vote.js" not in content
        assert ("Constitution" in content) == constitutional

    @pytest.mark.parametrize(
        ("view", "status"),
        [
            ("index", Bill.Status.OPEN),
            ("my-bills", Bill.Status.APPROVED),
            ("my-bills", Bill.Status.REJECTED),
            ("my-bills", Bill.Status.DRAFT),
            ("my-bill-votes", Bill.Status.OPEN),
            ("my-bill-votes", Bill.Status.FAILED),
        ],
    )
    def test_my_bills(self, status: Bill.Status, view: str, bill: Bill, client: Client):
        if view == "my-bill-votes":
            bill.vote(bill.author, support=True)
        bill.status = status
        bill.save()

        client.force_login(bill.author)
        response = client.get(reverse(f"webiscite:{view}"))
        content = response.content.decode()

        assert response.status_code == HTTPStatus.OK
        assert bill.name in content
        assert "Log in to vote" not in content
        assert "vote.js" in content
        assert (bill.get_status_display() in content) == (
            bill.status != Bill.Status.OPEN
        )
