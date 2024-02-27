import contextlib
from typing import Any

from django.db.models import Prefetch
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from democrasite.webiscite.models import Bill

from .serializers import BillSerializer


class BillViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.select_related("author", "pull_request")

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().retrieve(request, *args, **kwargs)

        if request.user.is_authenticated:
            bill: Bill = self.get_object()
            with contextlib.suppress(bill.vote_set.model.DoesNotExist):
                response.data["user_supports"] = bill.vote_set.get(
                    user=request.user
                ).support

        return response

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().list(request, *args, **kwargs)

        if request.user.is_authenticated:
            user_votes_prefetch = Prefetch(
                "vote_set", queryset=request.user.vote_set.all(), to_attr="user_votes"
            )

            bill_ids = [bill["id"] for bill in response.data]
            # Need a new database call in order to prefetch the user's votes
            bills = Bill.objects.filter(id__in=bill_ids).prefetch_related(
                user_votes_prefetch
            )
            for bill, bill_dict in zip(bills, response.data, strict=True):
                vote_query = bill.user_votes  # type: ignore [attr-defined]

                # Guaranteed to be at most one element, avoids calling database again
                for vote in vote_query:
                    bill_dict["user_supports"] = vote.support

        return response
