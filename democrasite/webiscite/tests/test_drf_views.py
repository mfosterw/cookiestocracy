from django.utils.timezone import get_current_timezone
from rest_framework.test import APIRequestFactory

from ..api.views import BillViewSet, PullRequestViewSet
from ..models import Bill, PullRequest


class TestPullRequestViewSet:
    def test_viewset_fields(self, api_rf: APIRequestFactory, user):
        pr = PullRequest.objects.create(
            pr_num=-1,
            title="Test PR",
            additions=0,
            deletions=0,
            sha="123",
            author_name=user.username,
        )

        view = PullRequestViewSet.as_view(actions={"get": "retrieve"})
        request = api_rf.get("/fake-url/")
        request.user = user

        response = view(request, pk=pr.pk)

        assert (
            response.data.items()
            >= {  # Subset of the response data
                "title": pr.title,
                "sha": pr.sha,
                "prop_date": pr.prop_date.astimezone(get_current_timezone()).isoformat(),
                "url": f"http://testserver/api/pull-requests/{pr.pk}/",
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
                "prop_date": bill.prop_date.astimezone(get_current_timezone()).isoformat(),
                "url": f"http://testserver/api/bills/{bill.pk}/",
            }.items()
        )
