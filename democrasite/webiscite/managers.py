"""Managers for the webiscite app models."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from logging import getLogger
from typing import TYPE_CHECKING
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule
from django_celery_beat.models import PeriodicTask

from democrasite.users.models import User

from .constitution import is_constitutional

logger = getLogger(__name__)

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
            },
        )

        pull_request.log("%s", "Created" if created else "Updated")
        return pull_request


class BillManager[T](models.Manager):
    def get_queryset(self):
        """Return a queryset with pull_request pre-fetched and vote percentages added.

        All Bill querysets include ``total_votes``, ``yes_percent``, and
        ``no_percent``
        annotations, and are ordered by creation date.
        """
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
            body: The body/description of the pull request
            author: The user who authored the pull request
            diff_text: The text of the diff of the pull request, used to determine
                whether the bill is constitutional
            pull_request: The pull request instance to associate with the bill

        Returns:
            The newly created bill instance
        """
        with self._create_submit_task() as submit_task:
            self._bill: Bill = self.model(
                name=title,
                description=body,
                author=author,
                pull_request=pull_request,
                status=self.model.Status.OPEN,
                constitutional=bool(is_constitutional(diff_text)),
                _submit_task=submit_task,
            )
            self._bill.full_clean()
            self._bill.save()
            bill = self._bill
            bill.log("Created")

        return bill

    @contextmanager
    def _create_submit_task(self) -> Iterator[PeriodicTask]:
        """Schedule a task to submit this bill for voting

        Returns:
            The task that was scheduled
        """
        # This might be better as a signal but I want to keep it localized
        voting_ends, __ = IntervalSchedule.objects.get_or_create(
            every=settings.WEBISCITE_VOTING_PERIOD, period=IntervalSchedule.DAYS
        )

        submit_task = PeriodicTask.objects.create(
            interval=voting_ends,
            name="bill_submit:temp",
            task="democrasite.webiscite.tasks.submit_bill",
            one_off=True,
            # If last_run_at is not set, the task will run relative to when the
            # scheduler started, not when it was created
            last_run_at=timezone.now(),
        )
        try:
            yield submit_task
        finally:
            if not (
                hasattr(self, "_bill")
                and hasattr(self._bill, "id")
                and isinstance(self._bill.id, int)
            ):
                raise AttributeError(
                    "self._bill was not saved in the submit task context"
                )

            submit_task.name = f"bill_submit:{self._bill.id}"
            submit_task.args = json.dumps([self._bill.id])
            submit_task.save()
            self._bill.log("Scheduled %s", submit_task.name)

            # Attribute could be shared between model instances
            del self._bill
