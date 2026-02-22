from logging import getLogger
from typing import TYPE_CHECKING
from typing import Any

from django.db import models

from democrasite.users.models import User

from .constitution import is_constitutional

logger = getLogger(__name__)

if TYPE_CHECKING:
    from .models import Bill  # pragma: no cover
    from .models import PullRequest  # pragma: no cover


class PullRequestManager[T](models.Manager):
    def create_from_github(self, pr: dict[str, Any]) -> T:
        """Create a :class:`~democrasite.webiscite.models.PullRequest` and optionally a
        :class:`~democrasite.webiscite.models.Bill` instance from a GitHub pull request

        Args:
            pr_args: The parameters for the ``PullRequest``
            bill_args: The parameters for the ``Bill`` or None

        Returns:
            A tuple containing the new or updated pull request and new bill instance, if
            applicable
        """
        pull_request, created = self.update_or_create(
            number=pr["number"],
            defaults={
                "title": pr["title"],
                "additions": pr["additions"],
                "deletions": pr["deletions"],
                "diff_url": pr["diff_url"],
                "author_name": pr["user"]["login"],
                "status": pr["state"],
                "sha": pr["head"]["sha"],
                "draft": pr.get("draft", False),
            },
        )

        pull_request.log("%s", "Created" if created else "Updated")
        return pull_request


class BillManager[T](models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("pull_request")
            .annotate(
                total_votes=models.Count("vote"),
                yes_percent=models.Case(
                    models.When(
                        models.Q(total_votes__gt=0),
                        100.0
                        * models.Count("vote", filter=models.Q(vote__support=True))
                        / models.F("total_votes"),
                    ),
                    default=models.Value(0),
                    output_field=models.FloatField(),
                ),
                no_percent=models.Case(
                    models.When(
                        models.Q(total_votes__gt=0),
                        100.0
                        * models.Count("vote", filter=models.Q(vote__support=False))
                        / models.F("total_votes"),
                    ),
                    default=models.Value(0),
                    output_field=models.FloatField(),
                ),
            )
            .order_by("created")
        )

    def annotate_user_vote(
        self, user: User, queryset: models.QuerySet["Bill"] | None = None
    ):
        if queryset is None:
            queryset = self.get_queryset()

        return queryset.annotate(
            user_vote=models.Subquery(
                queryset.filter(
                    vote__bill=models.OuterRef("pk"),
                    vote__user=user,
                ).values("vote__support")
            )
        )

    def create_from_github(
        self,
        title: str,
        body: str,
        author: User,
        diff_text: str,
        pull_request: "PullRequest",
    ) -> T:
        """Validate and create a :class:`~democrasite.webiscite.models.Bill` from a
        GitHub pull request

        Args:
            title: The title of the pull request
            body: The body of the pull request
            author: The user who created the pull request
            diff_text: The text of the diff of the pull request
            pull_request: The pull request instance to associate with the bill

        Returns:
            The new bill instance
        """

        status = (
            self.model.Status.DRAFT if pull_request.draft else self.model.Status.OPEN
        )

        bill = self.model(
            name=title,
            description=body,
            author=author,
            pull_request=pull_request,
            status=status,
            constitutional=bool(is_constitutional(diff_text)),
        )

        bill.full_clean()
        bill.save()
        bill.log("Created")

        return bill
