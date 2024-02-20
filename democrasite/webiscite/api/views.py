from django.contrib.auth import get_user_model
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from democrasite.webiscite.models import Bill, PullRequest

from .serializers import BillSerializer, PullRequestSerializer

User = get_user_model()


class PullRequestViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = PullRequestSerializer
    queryset = PullRequest.objects.all()


class BillViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.all()
