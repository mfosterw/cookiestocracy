from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from democrasite.webiscite.models import Bill

from .serializers import BillSerializer

User = get_user_model()


class BillViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.select_related("author", "pull_request")

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().retrieve(request, *args, **kwargs)

        if request.user.is_authenticated:
            bill: Bill = self.get_object()
            try:
                response.data["user_supports"] = bill.vote_set.get(user=request.user).support
            except bill.vote_set.model.DoesNotExist:
                pass

        return response

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().list(request, *args, **kwargs)

        if request.user.is_authenticated:
            user_votes_prefetch = Prefetch("vote_set", queryset=request.user.vote_set.all(), to_attr="user_votes")

            bill_ids = [bill["id"] for bill in response.data]
            # Need a new database call in order to prefetch the user's votes
            bills = Bill.objects.filter(id__in=bill_ids).prefetch_related(user_votes_prefetch)
            for bill, bill_dict in zip(bills, response.data):
                vote_query = bill.user_votes  # type: ignore [attr-defined]

                for vote in vote_query:  # Guaranteed to be at most one element, avoids calling database again
                    bill_dict["user_supports"] = vote.support

        return response
