from django.contrib.auth.models import AbstractBaseUser
from rest_framework.serializers import HyperlinkedModelSerializer, HyperlinkedRelatedField

from democrasite.webiscite.models import Bill, PullRequest


class PullRequestSerializer(HyperlinkedModelSerializer):
    bill_set: "HyperlinkedRelatedField[Bill]" = HyperlinkedRelatedField(
        view_name="bill-detail", many=True, read_only=True
    )

    class Meta:
        model = PullRequest
        fields = ["title", "author_name", "additions", "deletions", "sha", "time_created", "bill_set", "url"]

    def create(self, validated_data):
        raise NotImplementedError("Pull requests are read-only")

    def update(self, instance, validated_data):
        raise NotImplementedError("Pull requests are read-only")


class BillSerializer(HyperlinkedModelSerializer):
    yes_votes: "HyperlinkedRelatedField[AbstractBaseUser]" = HyperlinkedRelatedField(
        view_name="user-detail", many=True, lookup_field="username", read_only=True
    )
    no_votes: "HyperlinkedRelatedField[AbstractBaseUser]" = HyperlinkedRelatedField(
        view_name="user-detail", many=True, lookup_field="username", read_only=True
    )

    class Meta:
        model = Bill
        fields = ["name", "description", "time_created", "author", "pull_request", "yes_votes", "no_votes", "url"]
        extra_kwargs = {
            "author": {"lookup_field": "username", "read_only": True},
            "time_created": {"read_only": True},
        }
