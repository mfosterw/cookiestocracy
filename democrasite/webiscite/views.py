"""Views for the webiscite app."""

from http import HTTPStatus

from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from .models import Bill
from .models import ClosedBillVoteError


class BillListView(ListView):
    """View listing all open bills. Used for webiscite:index."""

    model = Bill

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Bill.objects.annotate_user_vote(self.request.user).filter(
                status=Bill.Status.OPEN
            )
        return Bill.objects.filter(status=Bill.Status.OPEN)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empty_message"] = "No bills up for vote right now."
        return context


bill_list_view = BillListView.as_view()


class BillProposalsView(LoginRequiredMixin, ListView):
    """View for listing bills proposed by the current user."""

    model = Bill

    def get_queryset(self):
        """
        Return the list of items for this view - bills proposed by the current user.
        """
        user = self.request.user
        assert user.is_authenticated  # type guard

        bill_set = user.bill_set.all()
        return Bill.objects.annotate_user_vote(user, bill_set)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "My Bills"
        context["empty_message"] = "You haven't proposed any bills yet."
        return context


bill_proposals_view = BillProposalsView.as_view()


class BillVotesView(LoginRequiredMixin, ListView):
    """View for listing bills voted on by the current user."""

    model = Bill

    def get_queryset(self):
        """
        Return the list of items for this view - bills voted on by the current user.
        """
        user = self.request.user
        assert user.is_authenticated  # type guard

        bills = user.votes.all()
        return Bill.objects.annotate_user_vote(user, bills)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "My Votes"
        context["empty_message"] = "You haven't voted on any bills yet."
        return context


bill_votes_view = BillVotesView.as_view()


class BillDetailView(DetailView):
    """View for one bill on its own page."""

    model = Bill

    def get_object(self, queryset=None):
        pk = self.kwargs.get("pk")

        if self.request.user.is_authenticated:
            return get_object_or_404(
                Bill.objects.annotate_user_vote(self.request.user), pk=pk
            )
        return get_object_or_404(Bill)


bill_detail_view = BillDetailView.as_view()


class BillUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """
    View for updating a bill's name and description on Democrasite
    """

    model = Bill
    fields = ["name", "description"]
    success_message = _("Information successfully updated")

    def test_func(self):
        return self.get_object().author == self.request.user


bill_update_view = BillUpdateView.as_view()


@require_POST
def vote_view(request: http.HttpRequest, pk: int) -> http.HttpResponse:
    """View for ajax request made when a user votes on a bill

    Validates that vote is valid and, if so, registers it with the database and returns
    an HttpResponse containing a JSON object listing the number of yes and no votes on
    that bill.

    Args:
        request: The request from the client
        pk: The id of the bill being voted on

    Returns:
        HttpResponse: A JsonResponse containing the vote counts for the bill if the
        request was valid, otherwise a client error response
    """
    if not request.user.is_authenticated:
        return http.HttpResponse("Login required", status=HTTPStatus.UNAUTHORIZED)

    vote_val = request.POST.get("vote")
    if not vote_val:
        return http.HttpResponseBadRequest('"vote" field is required.')

    vote = vote_val.lower()
    if vote == "vote-yes":
        support = True
    elif vote == "vote-no":
        support = False
    else:
        return http.HttpResponseBadRequest(
            '"vote" must be one of ("vote-yes", "vote-no").'
        )

    bill = Bill.objects.get(pk=pk)
    try:
        bill.vote(request.user, support=support)
    except ClosedBillVoteError as err:
        return http.HttpResponseForbidden(str(err))

    return http.JsonResponse(
        {
            "yes-votes": bill.yes_votes.count(),
            "no-votes": bill.no_votes.count(),
        }
    )
