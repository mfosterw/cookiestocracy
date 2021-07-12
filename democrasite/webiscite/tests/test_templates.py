"""Render each branch on each template to ensure there are no rendering errors."""
# pylint: disable=too-few-public-methods,no-self-use
from django.test import Client
from django.urls import reverse

from ..models import Bill
from .factories import BillFactory


class TestWebisciteTemplates:
    def test_bill_detail(self, client: Client, user):
        bill = BillFactory(state=Bill.CLOSED, author=user, constitutional=True)

        response = client.get(reverse("webiscite:bill-detail", args=(bill.id,)))

        assert response.status_code == 200
        assert response.templates[0].name == "webiscite/bill_detail.html"
        assert b"Log in to vote" not in response.content
        assert b"vote.js" not in response.content
        assert b"svg" not in response.content
        assert bill.get_state_display().encode() in response.content

        bill.state = Bill.OPEN
        bill.save()

        response = client.get(reverse("webiscite:bill-detail", args=(bill.id,)))

        assert b"Log in to vote" in response.content

        client.force_login(user)

        response = client.get(reverse("webiscite:bill-detail", args=(bill.id,)))

        assert b"vote.js" in response.content
        assert b"svg" in response.content
        assert bill.get_state_display().encode() not in response.content

    def test_bill_form(self, client: Client, user):
        bill = BillFactory(author=user)
        client.force_login(user)

        response = client.get(reverse("webiscite:bill-update", args=(bill.id,)))

        assert response.status_code == 200
        assert response.templates[0].name == "webiscite/bill_form.html"

    def test_bill_list_empty(self, client: Client, user):
        response = client.get(reverse("webiscite:index"))

        assert response.status_code == 200
        assert response.templates[0].name == "webiscite/bill_list.html"
        assert b"No bills" in response.content
        assert b"you haven't proposed any bills" not in response.content
        assert b"you haven't voted on any bills" not in response.content

        client.force_login(user)

        response = client.get(reverse("webiscite:my-bills"))

        assert b"No bills" not in response.content
        assert b"you haven't proposed any bills" in response.content
        assert b"you haven't voted on any bills" not in response.content

        response = client.get(reverse("webiscite:my-bill-votes"))

        assert b"No bills" not in response.content
        assert b"you haven't proposed any bills" not in response.content
        assert b"you haven't voted on any bills" in response.content

    def test_bill_list_populated(self, client: Client, user):
        bill = BillFactory(state=Bill.OPEN, author=user, constitutional=True)

        response = client.get(reverse("webiscite:index"))

        assert response.status_code == 200
        assert bill.name.encode() in response.content
        assert bill.get_state_display().encode() not in response.content
        assert b"Log in to vote" in response.content
        assert b"vote.js" not in response.content

        client.force_login(user)

        response = client.get(reverse("webiscite:index"))

        assert b"Log in to vote" not in response.content

        bill.state = Bill.CLOSED
        bill.save()

        response = client.get(reverse("webiscite:my-bills"))

        assert bill.name.encode() in response.content
        assert bill.get_state_display().encode() in response.content
        assert b"Log in to vote" not in response.content
        assert b"vote.js" in response.content
