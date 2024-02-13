from django.contrib.auth import get_user_model
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from democrasite.webiscite.models import Bill

from .serializers import BillSerializer

User = get_user_model()


class BillViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.all()
