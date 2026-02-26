"""Managers for the webiscite app models."""

from logging import WARNING
from typing import TYPE_CHECKING
from typing import Any

import requests
from django.db import models

from democrasite.users.models import User

from .constitution import is_constitutional

if TYPE_CHECKING:
    from .models import Bill  # pragma: no cover
    from .models import PullRequest  # pragma: no cover


class PullRequestManager[T](models.Manager):
    def create_from_github(self, pr: dict[str, Any]) -> T:
        """Create or update a :class:`~democrasite.webiscite.models.PullRequest` from
        a GitHub pull request payload

        Args:
            pr: The pull request data from the GitHub API

        Returns:
            The new or updated pull request instance
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
        """Return a queryset with related models pre-fetched and vote amounts added.

        All Bill querysets include ``total_votes``, ``yes_count``, ``yes_percent``,
        ``no_count`` and ``no_percent`` annotations, prefetch pull_request and author,
        and are ordered by creation date.
        """
        return (
            super()
            .get_queryset()
            .select_related("pull_request", "author")
            .annotate(
                total_votes=models.Count("vote"),
                yes_count=models.Count("vote", filter=models.Q(vote__support=True)),
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
                no_count=models.Count("vote", filter=models.Q(vote__support=False)),
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
        """Annotate a queryset with the given user's vote on each bill.

        Args:
            user: The user whose vote to annotate
            queryset: The queryset to annotate; defaults to ``self.get_queryset()``

        Returns:
            The queryset annotated with a ``user_vote`` field
            (``True``/``False``/``None``)
        """
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
        self, pull_request: "PullRequest", desc: str, author_uid: str
    ):
        """Validate and create a :class:`~democrasite.webiscite.models.Bill` from a
        GitHub pull request

        Args:
            pull_request: The pull request instance to associate with the bill
            desc: The description of the bill (pull request body)
            author_uid: The GitHub UID of the pull request author

        Returns:
            The new bill instance, or None if the author has no linked account
        """
        try:
            author = User.objects.filter(socialaccount__provider="github").get(
                socialaccount__uid=author_uid
            )
        except User.DoesNotExist:
            # If the creator of the pull request does not have a linked account,
            # a Bill cannot be created and the pr is ignored.
            pull_request.log("No bill created (user does not exist)", level=WARNING)
            return None

        diff_text = requests.get(pull_request.diff_url, timeout=10).text
        constitutional = bool(is_constitutional(diff_text))

        status = Bill.Status.DRAFT if pull_request.draft else Bill.Status.OPEN

        bill = self.model(
            name=pull_request.title,
            description=desc,
            author=author,
            pull_request=pull_request,
            status=status,
            constitutional=constitutional,
        )

        bill.full_clean()
        bill.save()
        bill.log("Created")

        return bill
