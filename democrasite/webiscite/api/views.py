from typing import Any

from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from democrasite.webiscite.models import Bill

from .serializers import BillSerializer


class BillViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.select_related("author", "pull_request")

    def get_serializer_context(self) -> dict[str, Any]:
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    # TODO: Prefetch bill list votes
