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
        draft = pull_request.draft
        with self._create_submit_task(enabled=not draft) as submit_task:
            self._bill: Bill = self.model(
                name=title,
                description=body,
                author=author,
                pull_request=pull_request,
                status=self.model.Status.DRAFT if draft else self.model.Status.OPEN,
                constitutional=bool(is_constitutional(diff_text)),
                _submit_task=submit_task,
            )
            self._bill.full_clean()
            self._bill.save()
            bill = self._bill
            bill.log("Created")

        return bill

    @contextmanager
    def _create_submit_task(self, *, enabled: bool = True) -> Iterator[PeriodicTask]:
        """Schedule a task to submit this bill for voting

        Args:
            enabled: Whether the task should be enabled immediately. Set to False
                for draft bills whose voting period hasn't started yet.

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
            enabled=enabled,
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
