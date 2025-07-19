from typing import Any

from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from drf_spectacular.utils import inline_serializer
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BooleanField
from rest_framework.serializers import IntegerField
from rest_framework.viewsets import GenericViewSet

from democrasite.webiscite.models import Bill

from .serializers import BillSerializer


class IsAuthorOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj: Bill) -> bool:
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        # IsAuthOrReadOnly
        if not request.user.is_authenticated:
            return False
        # All authenticated users can vote
        if request.resolver_match.view_name == "bill-vote":
            return True

        # Instance must have an attribute named `owner`.
        return obj.author == request.user


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
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_context(self) -> dict[str, Any]:
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    @action(detail=True, methods=("post",))
    def vote(self, request: Request, pk):
        bill: Bill = self.get_object()
        assert request.user.is_authenticated  # type guard
        bill.vote(request.user, support=request.data["support"])
        return Response(
            {"yes_votes": bill.yes_votes.count(), "no_votes": bill.no_votes.count()}
        )

    # TODO: Prefetch bill list votes
