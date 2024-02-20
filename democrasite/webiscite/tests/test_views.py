# pylint: disable=too-few-public-methods,no-self-use
import json

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from django.test import Client, RequestFactory
from django.urls import reverse

from democrasite.users.models import User

from ..models import Bill
from ..views import BillListView, BillProposalsView, BillVotesView, bill_detail_view, bill_update_view, vote_view
from .factories import BillFactory


class TestBillListView:
    def test_queryset(self):
        open_bill = BillFactory(state=Bill.States.OPEN)
        closed_bill = BillFactory(state=Bill.States.CLOSED)

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
    def test_get_queryset(self, rf: RequestFactory, bill: Bill):
        # Note that this function depends heavily on the vote method, which is tested in test_models.py
        user = bill.author  # could be any user, this is just for convenience
        request = rf.get("/fake-url/")
        request.user = user

        view = BillVotesView()
        view.request = request
        assert bill not in view.get_queryset()

        bill.vote(user, True)
        assert bill in view.get_queryset(), "Positive votes are included"

        bill.vote(user, False)
        assert bill in view.get_queryset(), "Negative votes are included"

        bill.vote(user, False)
        assert bill not in view.get_queryset(), "When a vote is undone it gets removed from queryset"


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

        assert isinstance(bad_response, HttpResponseRedirect)
        assert bad_response.status_code == 302
        assert bad_response.url == f"{reverse(settings.LOGIN_URL)}?next=/fake-url/"

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

    @pytest.mark.parametrize("data,status", [(None, 400), ({"vote": "idk"}, 400), ({"vote": "vote-yes"}, 403)])
    def test_not_open(self, user: User, rf: RequestFactory, data, status):
        request = rf.post("/fake-url/", data=data)
        request.user = user

        bill = BillFactory(state=Bill.States.CLOSED)
        response = vote_view(request, bill.id)

        assert response.status_code == status
        if data is None:
            assert response.content == b'"vote" data expected'
        elif data["vote"] == "idk":
            assert response.content == b'"vote" must be one of ("vote-yes", "vote-no")'
        else:
            assert response.content == b"Bill may not be voted on"

    @pytest.mark.parametrize("vote", ["vote-yes", "vote-no"])
    def test_vote(self, rf: RequestFactory, user: User, bill: Bill, vote):
        request = rf.post("/fake-url/", data={"vote": vote})
        request.user = user

        response = vote_view(request, bill.id)

        assert response.status_code == 200

        data = json.loads(response.content)
        assert data["yes-votes"] == (1 if vote == "vote-yes" else 0)
        assert data["no-votes"] == (1 if vote == "vote-no" else 0)
        assert user.votes.filter(pk=bill.pk).exists()
