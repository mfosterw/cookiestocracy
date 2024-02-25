"""URLs for Webiscite views."""

from django.urls import path

from . import views
from .webhooks import github_webhook_view

app_name = "webiscite"
urlpatterns = [
    path("", views.bill_list_view, name="index"),
    path("proposals/", views.bill_proposals_view, name="my-bills"),
    path("votes/", views.bill_votes_view, name="my-bill-votes"),
    path("bills/<int:pk>/", views.bill_detail_view, name="bill-detail"),
    path("bills/<int:pk>/update/", views.bill_update_view, name="bill-update"),
    path("bills/<int:pk>/vote/", views.vote_view, name="bill-vote"),
    path("hooks/github/", github_webhook_view, name="github-webhook"),
]
