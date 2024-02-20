import pytest
from django.utils.timezone import get_current_timezone
from rest_framework.test import APIRequestFactory

from democrasite.webiscite.api.serializers import PullRequestSerializer
from democrasite.webiscite.tests.factories import PullRequestFactory

from ..api.views import BillViewSet, PullRequestViewSet
from ..models import Bill


class TestPullRequestSerializer:
    def test_serializer_read_only(self):
        serializer = PullRequestSerializer(PullRequestFactory())
        with pytest.raises(NotImplementedError):
            serializer.create({})
        with pytest.raises(NotImplementedError):
            assert serializer.update({}, {})


class TestPullRequestViewSet:
    def test_viewset_fields(self, api_rf: APIRequestFactory, user):
        pull_request = PullRequestFactory()

        view = PullRequestViewSet.as_view(actions={"get": "retrieve"})
        request = api_rf.get("/fake-url/")
        request.user = user

        response = view(request, pk=pull_request.number)

        assert (
            response.data.items()
            >= {  # Subset of the response data
                "title": pull_request.title,
                "sha": pull_request.sha,
                "time_created": pull_request.time_created.astimezone(get_current_timezone()).isoformat(),
                "url": f"http://testserver/api/pull-requests/{pull_request.number}/",
            }.items()
        )


class TestBillViewSet:
    def test_viewset_fields(self, bill: Bill, api_rf: APIRequestFactory):
        bill.vote(bill.author, True)

        view = BillViewSet.as_view(actions={"get": "retrieve"})
        request = api_rf.get("/fake-url/")
        request.user = bill.author

        response = view(request, pk=bill.pk)

        assert (
            response.data.items()
            >= {  # Subset of the response data
                "name": bill.name,
                "description": bill.description,
                "time_created": bill.time_created.astimezone(get_current_timezone()).isoformat(),
                "url": f"http://testserver/api/bills/{bill.pk}/",
            }.items()
        )
