from rest_framework.serializers import CharField
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SlugRelatedField

from democrasite.users.api.serializers import UserSerializer
from democrasite.users.models import User
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import PullRequest


class PullRequestSerializer(ModelSerializer):
    class Meta:
        model = PullRequest
        fields = ["number", "title", "additions", "deletions", "time_created"]
        read_only_fields = fields  # pull requests are read-only


class BillSerializer(ModelSerializer):
    author = UserSerializer()
    pull_request = PullRequestSerializer(read_only=True)
    state = CharField(source="get_state_display")

    yes_votes: SlugRelatedField[User] = SlugRelatedField(
        many=True, read_only=True, slug_field="username"
    )
    no_votes: SlugRelatedField[User] = SlugRelatedField(
        many=True, read_only=True, slug_field="username"
    )

    class Meta:
        model = Bill
        exclude = ["votes", "time_updated", "submit_task"]
        read_only_fields = [
            "author",
            "pull_request",
            "state",
            "constitutional",
            "time_created",
            "yes_votes",
            "no_votes",
        ]
