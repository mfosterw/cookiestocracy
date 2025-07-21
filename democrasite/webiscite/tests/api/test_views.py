from http import HTTPStatus

from django.urls import reverse
from django.utils.timezone import get_current_timezone
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory

from democrasite.webiscite.api.views import BillViewSet
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import User
from democrasite.webiscite.tests.factories import BillFactory


class TestPermissions:
    def test_unauthenticated(self, bill: Bill, api_rf: APIRequestFactory):
        view = BillViewSet.as_view(actions={"post": "update"})
        request = api_rf.post("/fake-url/", {"description": "new description"})
        old_description = bill.description

        response = view(request, pk=bill.pk)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.data["detail"].code == "not_authenticated"
        assert bill.description == old_description

    def test_not_author(
        self, bill: Bill, user: User, api_rf: APIRequestFactory, api_client: APIClient
    ):
        api_client.force_login(user)
        url = reverse("bill-detail", args=[bill.id])
        old_description = bill.description

        response = api_client.put(url, {"description": "new description"})

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.data["detail"].code == "permission_denied"
        assert bill.description == old_description


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
                "status": "Open",
                "created": bill.created.astimezone(get_current_timezone()).isoformat(),
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

    def test_retrieve_user_supports(self, bill: Bill, api_rf: APIRequestFactory):
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

    def test_update(self, bill: Bill, api_client: APIClient):
        api_client.force_login(bill.author)
        url = reverse("bill-detail", args=[bill.id])
        new_description = "new description"

        response = api_client.patch(url, {"description": new_description})

        assert response.data["name"] == bill.name

        bill.refresh_from_db()
        assert bill.description == new_description

    def test_vote(self, bill: Bill, user: User, api_client: APIClient):
        api_client.force_login(user)
        url = reverse("bill-vote", args=[bill.id])

        response = api_client.post(url, {"support": True})

        assert response.status_code == HTTPStatus.OK
        assert response.data["yes_votes"] == 1
        assert response.data["no_votes"] == 0
        assert bill.yes_votes.filter(pk=user.pk).exists()

    def test_vote_no_data(self, bill: Bill, api_client: APIClient):
        api_client.force_login(bill.author)
        url = reverse("bill-vote", args=[bill.id])

        response = api_client.post(url)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data[0].code == "invalid"
        assert not bill.yes_votes.filter(pk=bill.author.pk).exists()

    def test_vote_bad_data(self, bill: Bill, api_client: APIClient):
        api_client.force_login(bill.author)
        url = reverse("bill-vote", args=[bill.id])

        response = api_client.post(url, {"support": "banana"})

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data[0].code == "invalid"
        assert not bill.yes_votes.filter(pk=bill.author.pk).exists()
