from django.urls import resolve, reverse


def test_bill_list():
    assert reverse("bill-list") == "/api/bills/"
    assert resolve("/api/bills/").view_name == "bill-list"


def test_bill_detail(bill):
    assert reverse("bill-detail", kwargs={"pk": bill.pk}) == f"/api/bills/{bill.pk}/"
    assert resolve(f"/api/bills/{bill.pk}/").view_name == "bill-detail"
