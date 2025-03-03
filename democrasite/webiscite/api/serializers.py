from typing import TYPE_CHECKING

from rest_framework.serializers import CharField
from rest_framework.serializers import IntegerField
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SerializerMethodField

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

    yes_votes = IntegerField(read_only=True, source="yes_votes.count")
    no_votes = IntegerField(read_only=True, source="no_votes.count")
    user_supports = SerializerMethodField(required=False)

    class Meta:
        model = Bill
        exclude = ["votes", "modified", "_submit_task"]
        read_only_fields = [
            "author",
            "pull_request",
            "status",
            "constitutional",
            "created",
            "yes_votes",
            "no_votes",
            "user_supports",
        ]

    def get_user_supports(self, bill: Bill) -> bool | None:
        """Return whether the user supports the bill. If the user is not authenticated
        or has not voted on this bill, return None.

        Args:
            bill: The bill to check

        Returns:
            Whether the user supports the bill, or None if not applicable"""
        user: User = self.context["user"]
        return bill.user_supports(user) if user.is_authenticated else None
