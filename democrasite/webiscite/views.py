"""Views for the webiscite app."""

from http import HTTPStatus

from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from .models import Bill

# Bill-related views


class BillListView(ListView):
    """View listing all open bills. Used for webiscite:index."""

    model = Bill
    queryset = Bill.objects.filter(status=Bill.Status.OPEN)

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
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.bill_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "My Bills"
        context["empty_message"] = "Looks like you haven't proposed any bills yet."
        return context


bill_proposals_view = BillProposalsView.as_view()


class BillVotesView(LoginRequiredMixin, ListView):
    """View for listing bills voted on by the current user."""

    model = Bill

    def get_queryset(self):
        """
        Return the list of items for this view - bills voted on by the current user.
        """
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.votes.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "My Votes"
        context["empty_message"] = "Looks like you haven't voted on any bills yet."
        return context


bill_votes_view = BillVotesView.as_view()


class BillDetailView(DetailView):
    """View for one bill on its own page."""

    model = Bill


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
        return http.HttpResponseBadRequest('"vote" data expected')
    if vote_val not in {"vote-yes", "vote-no"}:
        return http.HttpResponseBadRequest(
            '"vote" must be one of ("vote-yes", "vote-no")'
        )

    bill = Bill.objects.get(pk=pk)
    if bill.status != Bill.Status.OPEN:
        return http.HttpResponseForbidden("Bill may not be voted on")

    if vote_val == "vote-yes":
        bill.vote(request.user, support=True)
    elif vote_val == "vote-no":
        bill.vote(request.user, support=False)

    return http.JsonResponse(
        {
            "yes-votes": bill.yes_votes.count(),
            "no-votes": bill.no_votes.count(),
        }
    )
