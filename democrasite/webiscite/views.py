"""Views for the webiscite app."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, UpdateView

from .models import Bill

# Bill-related views


class BillListView(ListView):
    """View listing all open bills. Used for webiscite:index."""

    model = Bill
    queryset = Bill.objects.filter(state=Bill.States.OPEN)

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
        return self.request.user.bill_set.all()  # type: ignore [union-attr]

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
        assert self.request.user.is_authenticated
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


# Use vote_view below, this would be decorated if possible
@require_POST
def vote_view(request: HttpRequest, pk: int) -> HttpResponse:
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
        return HttpResponse("Login required", status=401)  # 401 means unauthorized

    vote_val = request.POST.get("vote")
    if not vote_val:
        return HttpResponseBadRequest('"vote" data expected')
    elif vote_val not in {"vote-yes", "vote-no"}:
        return HttpResponseBadRequest('"vote" must be one of ("vote-yes", "vote-no")')

    bill = Bill.objects.get(pk=pk)
    if bill.state != Bill.States.OPEN:
        return HttpResponseForbidden("Bill may not be voted on")  # status 403

    if vote_val == "vote-yes":
        bill.vote(request.user, True)
    elif vote_val == "vote-no":
        bill.vote(request.user, False)

    return JsonResponse(
        {
            "yes-votes": bill.yes_votes.count(),
            "no-votes": bill.no_votes.count(),
        }
    )
