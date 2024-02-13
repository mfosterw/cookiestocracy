from django.urls import resolve, reverse


def test_bill_list():
    assert reverse("api:bill-list") == "/api/bills/"
    assert resolve("/api/bills/").view_name == "api:bill-list"


def test_bill_detail(bill):
    assert reverse("api:bill-detail", kwargs={"pk": bill.pk}) == f"/api/bills/{bill.pk}/"
    assert resolve(f"/api/bills/{bill.pk}/").view_name == "api:bill-detail"
