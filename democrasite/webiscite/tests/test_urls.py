import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import resolve, reverse
from github import Auth, Github

from ..models import Bill


def test_index():
    assert reverse("webiscite:index") == "/"
    assert resolve("/").view_name == "webiscite:index"


def test_proposals():
    assert reverse("webiscite:my-bills") == "/proposals/"
    assert resolve("/proposals/").view_name == "webiscite:my-bills"


def test_votes():
    assert reverse("webiscite:my-bill-votes") == "/votes/"
    assert resolve("/votes/").view_name == "webiscite:my-bill-votes"


def test_detail(bill: Bill):
    assert (
        reverse("webiscite:bill-detail", kwargs={"pk": bill.id}) == f"/bills/{bill.id}/"
    )
    assert resolve(f"/bills/{bill.id}/").view_name == "webiscite:bill-detail"


def test_update(bill: Bill):
    assert (
        reverse("webiscite:bill-update", kwargs={"pk": bill.id})
        == f"/bills/{bill.id}/update/"
    )
    assert resolve(f"/bills/{bill.id}/update/").view_name == "webiscite:bill-update"


def test_vote(bill: Bill):
    assert (
        reverse("webiscite:bill-vote", kwargs={"pk": bill.id})
        == f"/bills/{bill.id}/vote/"
    )
    assert resolve(f"/bills/{bill.id}/vote/").view_name == "webiscite:bill-vote"


@pytest.mark.skipif(
    settings.WEBISCITE_GITHUB_TOKEN is None, reason="requires Github token"
)
def test_github_hook():
    hook_urls = []
    repo = Github(auth=Auth.Token(settings.WEBISCITE_GITHUB_TOKEN)).get_repo(
        settings.WEBISCITE_REPO
    )
    for hook in repo.get_hooks():
        hook_urls.append(hook.config["url"])

    assert any(
        (Site.objects.get(id=settings.SITE_ID).domain + "/hooks/github/") in url
        for url in hook_urls
    )
