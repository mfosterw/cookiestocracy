# pylint: disable=too-few-public-methods,no-self-use
import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import Client, RequestFactory
from django.urls import reverse

from democrasite.users.models import User
from democrasite.users.tests.factories import UserFactory

from ..models import Bill
from ..views import (
    BillListView,
    BillProposalsView,
    BillVotesView,
    bill_detail_view,
    bill_update_view,
    vote_view,
)
from .factories import BillFactory


class TestBillListView:
    def test_queryset(self):
        open_bill = BillFactory(state=Bill.OPEN)
        closed_bill = BillFactory(state=Bill.CLOSED)

        assert open_bill in BillListView.queryset
        assert closed_bill not in BillListView.queryset


class TestBillProposalsView:
    def test_get_queryset(self, bill: Bill, rf: RequestFactory):
        assert bill.author is not None  # Silences mypy and better than ignore imo

        view = BillProposalsView()
        request = rf.get("/fake-url/")

        request.user = bill.author
        view.request = request

        assert bill in view.get_queryset()

        bad_bill = BillFactory()
        assert bad_bill not in view.get_queryset()


class TestBillVotesView:
    def test_get_queryset(self, rf: RequestFactory):
        views = (BillVotesView(), BillVotesView())
        bills = (BillFactory(state=Bill.OPEN), BillFactory(state=Bill.OPEN))
        users = (UserFactory(), UserFactory())
        requests = (rf.get("/fake-url/"), rf.get("/fake-url/"))

        # Make sure positive votes are included
        bills[0].vote(True, users[0])

        requests[0].user = users[0]
        views[0].request = requests[0]

        assert bills[0] in views[0].get_queryset()
        assert bills[1] not in views[0].get_queryset()

        # Make sure negative votes are included
        bills[0].vote(False, users[1])

        requests[1].user = users[1]
        views[1].request = requests[1]

        assert bills[0] in views[1].get_queryset()
        assert bills[1] not in views[1].get_queryset()

        # Make sure when a vote is undone it gets removed from queryset
        bills[0].vote(True, users[0])
        assert bills[0] not in views[0].get_queryset()


class TestBillDetailView:
    def test_view_response(self, bill: Bill, rf: RequestFactory):
        # Basically just test the view exists, just to have a test for it
        request = rf.get("/fake-url/")
        response = bill_detail_view(request, pk=bill.id)
        assert response.status_code == 200


class TestBillUpdateView:
    def test_test_func(self, bill: Bill, rf: RequestFactory):
        assert bill.author is not None  # Also silences mypy

        # Expect redirect because request fails test
        bad_request = rf.get("/fake-url/")
        bad_request.user = AnonymousUser()

        bad_response = bill_update_view(bad_request, pk=bill.id)

        assert bad_response.status_code == 302
        assert bad_response.url == reverse(settings.LOGIN_URL) + "?next=/fake-url/"

        # Expect success response because request passes test
        good_request = rf.get("/fake-url/")
        good_request.user = bill.author

        good_response = bill_update_view(good_request, pk=bill.id)

        assert good_response.status_code == 200

    def test_messages(self, bill: Bill, client: Client):
        """Tests that bills update and emit proper messages afterwards"""
        assert bill.author is not None  # Silences mypy
        client.force_login(bill.author)

        response = client.post(
            reverse("webiscite:bill-update", kwargs={"pk": bill.id}),
            data={"name": "test", "description": "testing"},
            follow=True,
        )

        messages_sent = [m.message for m in response.context["messages"]]
        assert messages_sent == ["Information successfully updated"]


class TestVoteView:
    # I'd normally give a method-based view method-based tests, but this has many tests
    def test_not_authenticated(self, rf: RequestFactory):
        request = rf.post("/fake-url/")
        request.user = AnonymousUser()

        response = vote_view(request, 0)

        assert response.status_code == 401
        assert response.content == b"Login required"

    def test_not_open(self, user: User, rf: RequestFactory):
        request = rf.post("/fake-url/")
        request.user = user

        bill = BillFactory(state=Bill.CLOSED)
        response = vote_view(request, bill.id)

        assert response.status_code == 403
        assert response.content == b"Bill may not be voted on"

    def test_vote_not_present(self, user: User, rf: RequestFactory):
        request = rf.post("/fake-url/")
        request.user = user

        bill = BillFactory(state=Bill.OPEN)
        response = vote_view(request, bill.id)

        assert response.status_code == 400
        assert response.content == b'"vote" data expected'

    def test_invalid_vote(self, user: User, rf: RequestFactory):
        request = rf.post("/fake-url/", data={"vote": "idk"})
        request.user = user

        bill = BillFactory(state=Bill.OPEN)
        response = vote_view(request, bill.id)

        assert response.status_code == 400
        assert response.content == b'"vote" must be one of ("vote-yes", "vote-no")'

    def test_vote_yes(self, user: User, rf: RequestFactory):
        request = rf.post("/fake-url/", data={"vote": "vote-yes"})
        request.user = user

        bill = BillFactory(state=Bill.OPEN)
        response = vote_view(request, bill.id)

        assert response.status_code == 200

        data = json.loads(response.content)
        assert data["yes-votes"] == 1
        assert data["no-votes"] == 0
        assert bill.yes_votes.filter(pk=user.pk).exists()

    def test_vote_no(self, user: User, rf: RequestFactory):
        request = rf.post("/fake-url/", data={"vote": "vote-no"})
        request.user = user

        bill = BillFactory(state=Bill.OPEN)
        response = vote_view(request, bill.id)

        assert response.status_code == 200

        data = json.loads(response.content)
        assert data["yes-votes"] == 0
        assert data["no-votes"] == 1
        assert bill.no_votes.filter(pk=user.pk).exists()
