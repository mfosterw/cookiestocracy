from typing import TYPE_CHECKING

from rest_framework.serializers import CharField
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SlugRelatedField

from democrasite.users.api.serializers import UserSerializer
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import PullRequest

if TYPE_CHECKING:
    from democrasite.users.models import User  # pragma: no cover


class PullRequestSerializer(ModelSerializer):
    class Meta:
        model = PullRequest
        fields = [
            "number",
            "title",
            "additions",
            "deletions",
            "diff_url",
            "created",
        ]
        read_only_fields = fields  # pull requests are read-only


class BillSerializer(ModelSerializer):
    author = UserSerializer()
    pull_request = PullRequestSerializer(read_only=True)
    status = CharField(source="get_status_display")

    yes_votes: "SlugRelatedField[User]" = SlugRelatedField(
        many=True, read_only=True, slug_field="username"
    )
    no_votes: "SlugRelatedField[User]" = SlugRelatedField(
        many=True, read_only=True, slug_field="username"
    )

    class Meta:
        model = Bill
        exclude = ["votes", "modified", "submit_task"]
        read_only_fields = [
            "author",
            "pull_request",
            "status",
            "constitutional",
            "created",
            "yes_votes",
            "no_votes",
        ]
