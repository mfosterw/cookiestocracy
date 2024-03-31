from typing import Any
from typing import cast

from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from drf_spectacular.utils import inline_serializer
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BooleanField
from rest_framework.serializers import IntegerField
from rest_framework.viewsets import GenericViewSet

from democrasite.users.models import User
from democrasite.webiscite.models import Bill

from .serializers import BillSerializer


@extend_schema_view(
    vote=extend_schema(
        request=inline_serializer(
            "Vote", fields={"support": BooleanField(required=True)}
        ),
        responses=inline_serializer(
            "VoteCounts",
            fields={"yes_votes": IntegerField(), "no_votes": IntegerField()},
        ),
    )
)
class BillViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.select_related("author", "pull_request")

    def get_serializer_context(self) -> dict[str, Any]:
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    @action(detail=True, methods=("post",))
    def vote(self, request: Request, pk):
        bill: Bill = self.get_object()
        bill.vote(cast(User, request.user), support=request.data["support"])
        return Response(
            {"yes_votes": bill.yes_votes.count(), "no_votes": bill.no_votes.count()}
        )

    # TODO: Prefetch bill list votes
