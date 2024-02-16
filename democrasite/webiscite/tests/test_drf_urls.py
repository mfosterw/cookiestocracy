from django.urls import resolve, reverse

from ..models import Bill, PullRequest


def test_pull_request_list():
    assert reverse("pullrequest-list") == "/api/pull-requests/"
    assert resolve("/api/pull-requests/").view_name == "pullrequest-list"


def test_pull_request_detail():
    pr = PullRequest.objects.create(
        pr_num=-1, title="Test PR", author_name="test", state="open", additions=0, deletions=0, sha="0" * 40
    )
    assert reverse("pullrequest-detail", kwargs={"pk": pr.pk}) == f"/api/pull-requests/{pr.pk}/"
    assert resolve(f"/api/pull-requests/{pr.pk}/").view_name == "pullrequest-detail"


def test_bill_list():
    assert reverse("bill-list") == "/api/bills/"
    assert resolve("/api/bills/").view_name == "bill-list"


def test_bill_detail(bill: Bill):
    assert reverse("bill-detail", kwargs={"pk": bill.pk}) == f"/api/bills/{bill.pk}/"
    assert resolve(f"/api/bills/{bill.pk}/").view_name == "bill-detail"
