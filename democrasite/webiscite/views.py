"""Views for the webiscite app."""

from collections.abc import Callable

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, UpdateView

from .models import Bill

# Bill-related views


class BillListView(ListView):
    """
    View listing all open bills. Used for webiscite:index.
    """

    model = Bill
    queryset = Bill.objects.filter(state=Bill.OPEN)


bill_list_view = BillListView.as_view()


class BillProposalsView(LoginRequiredMixin, ListView):
    """
    View for listing bills proposed by the current user.
    """

    model = Bill

    def get_queryset(self):
        """
        Return the list of items for this view – bills proposed by the current user.
        """
        return self.request.user.bill_set.all()  # type: ignore [union-attr]


bill_proposals_view = BillProposalsView.as_view()


class BillVotesView(LoginRequiredMixin, ListView):
    """
    View for listing bills voted on by the current user.
    """

    model = Bill

    def get_queryset(self):
        """
        Return the list of items for this view - bills voted on by the current user.
        """
        return self.request.user.yes_votes.all() | self.request.user.no_votes.all()  # type: ignore [union-attr]


bill_votes_view = BillVotesView.as_view()


class BillDetailView(DetailView):
    """
    View for one bill on its own page
    """

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
        return self.get_object().author == self.request.user  # type: ignore [attr-defined]


bill_update_view = BillUpdateView.as_view()


# Use vote_view below, this would be decorated if possible
def _vote_view(request: HttpRequest, pk: int) -> HttpResponse:
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

    bill = Bill.objects.get(pk=pk)
    if bill.state != Bill.OPEN:
        return HttpResponseForbidden("Bill may not be voted on")  # status 403

    vote_val = request.POST.get("vote")
    if not vote_val:
        return HttpResponseBadRequest('"vote" data expected')

    if vote_val == "vote-yes":
        bill.vote(True, request.user)
    elif vote_val == "vote-no":
        bill.vote(False, request.user)
    else:
        return HttpResponseBadRequest('"vote" must be one of ("vote-yes", "vote-no")')

    return JsonResponse(
        {
            "yes-votes": bill.yes_votes.count(),
            "no-votes": bill.no_votes.count(),
        }
    )


# mypy has trouble with decorators so I needed a workaround to annotate this
vote_view: Callable[[HttpRequest, int], HttpResponse] = require_POST(_vote_view)
