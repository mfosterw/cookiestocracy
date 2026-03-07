from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from drf_spectacular.utils import inline_serializer
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BooleanField
from rest_framework.serializers import IntegerField
from rest_framework.serializers import ValidationError as RestValidationError
from rest_framework.viewsets import GenericViewSet

from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import ClosedBillVoteError

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
        # IsAuthenticatedOrReadOnly
        if not request.user.is_authenticated:
            return False

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
    queryset = Bill.objects.all()
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    @action(detail=True, methods=("post",), permission_classes=(IsAuthenticated,))
    def vote(self, request: Request, pk):
        # TODO: unify with democrasite/webiscite.py::vote_view?
        assert request.user.is_authenticated  # type guard, get_object checks login

        vote_data = request.data.get("support")
        if not vote_data:
            raise RestValidationError({"support": "This field is required."})

        vote = vote_data.lower()
        if vote == "true":
            support = True
        elif vote == "false":
            support = False
        else:
            raise RestValidationError({"support": 'support must be "true" or "false".'})

        bill: Bill = self.get_object()
        try:
            bill.vote(request.user, support=support)
        except ClosedBillVoteError as err:
            raise PermissionDenied(str(err)) from err

        bill = Bill.objects.get(pk=pk)
        return Response({"yes_votes": bill.yes_count, "no_votes": bill.no_count})

    # TODO: Prefetch bill list votes
