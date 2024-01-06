"""URLs for Webiscite views."""
from django.urls import path

from .views import (
    bill_detail_view,
    bill_list_view,
    bill_proposals_view,
    bill_update_view,
    bill_votes_view,
    vote_view,
)
from .webhooks import github_hook

app_name = "webiscite"
urlpatterns = [
    path("", bill_list_view, name="index"),
    path("proposals/", bill_proposals_view, name="my-bills"),
    path("votes/", bill_votes_view, name="my-bill-votes"),
    path("bills/<int:pk>/", bill_detail_view, name="bill-detail"),
    path("bills/<int:pk>/update/", bill_update_view, name="bill-update"),
    path("bills/<int:pk>/vote/", vote_view, name="bill-vote"),
    path("hooks/github/", github_hook),
]
