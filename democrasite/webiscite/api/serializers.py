from django.contrib.auth.models import AbstractBaseUser
from rest_framework.serializers import HyperlinkedModelSerializer, HyperlinkedRelatedField, PrimaryKeyRelatedField

from democrasite.webiscite.models import Bill, PullRequest


class BillSerializer(HyperlinkedModelSerializer):
    yes_votes: "HyperlinkedRelatedField[AbstractBaseUser]" = HyperlinkedRelatedField(
        view_name="user-detail", many=True, lookup_field="username", read_only=True
    )
    no_votes: "HyperlinkedRelatedField[AbstractBaseUser]" = HyperlinkedRelatedField(
        view_name="user-detail", many=True, lookup_field="username", read_only=True
    )
    pull_request: "PrimaryKeyRelatedField[PullRequest]" = PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Bill
        fields = ["name", "description", "prop_date", "author", "pull_request", "yes_votes", "no_votes", "url"]
        extra_kwargs = {
            "author": {"lookup_field": "username", "read_only": True},
            "prop_date": {"read_only": True},
        }
