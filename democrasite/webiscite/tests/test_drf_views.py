from django.utils.timezone import get_current_timezone
from rest_framework.test import APIRequestFactory

from democrasite.webiscite.api.views import BillViewSet
from democrasite.webiscite.models import Bill
from democrasite.webiscite.tests.factories import BillFactory


class TestBillViewSet:
    def test_viewset_fields(self, bill: Bill, api_rf: APIRequestFactory):
        view = BillViewSet.as_view(actions={"get": "retrieve"})
        request = api_rf.get("/fake-url/")
        request.user = bill.author

        response = view(request, pk=bill.pk)

        assert (
            response.data.items()
            >= {  # Subset of the response data
                "name": bill.name,
                "description": bill.description,
                "state": "Open",
                "time_created": bill.time_created.astimezone(
                    get_current_timezone()
                ).isoformat(),
            }.items()
        )

    def test_retrieve_user_supports_undefined(
        self, bill: Bill, api_rf: APIRequestFactory
    ):
        view = BillViewSet.as_view(actions={"get": "retrieve"})
        request = api_rf.get("/fake-url/")
        request.user = bill.author

        response = view(request, pk=bill.pk)

        assert response.data.get("user_supports") is None

    def test_retrieve_user_supports_true(self, bill: Bill, api_rf: APIRequestFactory):
        bill.vote(bill.author, support=True)

        view = BillViewSet.as_view(actions={"get": "retrieve"})
        request = api_rf.get("/fake-url/")
        request.user = bill.author

        response = view(request, pk=bill.pk)

        assert response.data["user_supports"] is True

    def test_list(self, api_rf: APIRequestFactory):
        batch_size = 2
        bills = BillFactory.create_batch(batch_size)
        bills[0].vote(bills[0].author, support=False)

        view = BillViewSet.as_view(actions={"get": "list"})
        request = api_rf.get("/fake-url/")
        request.user = bills[0].author

        response = view(request)

        assert len(response.data) == batch_size
        assert response.data[0]["name"] == bills[0].name
        assert response.data[0].get("user_supports") is False
        assert response.data[1].get("user_supports") is None
