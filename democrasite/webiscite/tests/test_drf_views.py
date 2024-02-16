from ..api.views import BillViewSet


class TestBillViewSet:
    def test_viewset_fields(self, bill, api_rf):
        bill.vote(bill.author, True)

        view = BillViewSet()
        request = api_rf.get("/fake-url/")

        view.request = request

        assert view.get_queryset().first() == bill
