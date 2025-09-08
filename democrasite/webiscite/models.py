"""Models for the webiscite app"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from logging import getLogger
from typing import Any

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import IntervalSchedule
from django_celery_beat.models import PeriodicTask
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from democrasite.users.models import User

from .constitution import is_constitutional

logger = getLogger(__name__)


class ClosedBillVoteError(Exception):
    pass


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
            },
        )

        action = "created" if created else "updated"
        logger.info("PR %s: Pull request %s", pr["number"], action)
        return pull_request


class PullRequest(TimeStampedModel):
    """Local representation of a pull request on Github"""

    number = models.IntegerField(_("Pull request number"), primary_key=True)
    title = models.CharField(max_length=100)
    additions = models.IntegerField(help_text=_("Lines added"))
    deletions = models.IntegerField(help_text=_("Lines removed"))
    diff_url = models.URLField(help_text=_("URL to the diff of the pull request"))
    # Store Github username of author even if they are not a user on the site
    author_name = models.CharField(max_length=100)
    #:
    status = models.CharField(
        max_length=6,
        choices=(("closed", _("Closed")), ("open", _("Open"))),
        help_text=_("State of the PR on Github"),
    )
    # Unique by defintion but added the constraint for clarity
    sha = models.CharField(
        max_length=40, unique=True, help_text=_("Unique identifier of PR commit")
    )

    history = HistoricalRecords()

    objects = PullRequestManager()

    def __str__(self) -> str:
        return f"PR #{self.number}"

    def close(self) -> "Bill | None":
        """Mark the pull request and the associated bill closed if it was open

        Args:
            pr_num: The number of the pull request to close

        Returns:
            The bill associated with the pull request, if it was open
        """
        self.status = "closed"
        self.save()

        try:
            bill: Bill = self.bill_set.get(status=Bill.Status.OPEN)
        except Bill.DoesNotExist:
            logger.info("PR %s: No open bill found", self.number)
            return None
        else:
            bill.close()
            return bill


class Vote(models.Model):
    """A vote for or against a bill, with a timestamp"""

    bill = models.ForeignKey("Bill", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    support = models.BooleanField()
    when = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("bill", "user"),
                name="unique_user_bill_vote",
                violation_error_code=_("Only one vote per user per bill allowed"),
            )  # type: ignore[call-overload]
        ]

    def __str__(self) -> str:
        return f"{self.user} {'for' if self.support else 'against'} {self.bill}"


class BillManager[T](models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
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
        pull_request: PullRequest,
    ) -> T:
        """Validate and create a :class:`~democrasite.webiscite.models.Bill` from a
        GitHub pull request

        Args:
            pr: The pull request data from the GitHub API
            diff_text: The text of the diff of the pull request
            pull_request: The pull request instance to associate with the bill

        Returns:
            A tuple containing the new or update pull request and new bill instance, if
            applicable
        """
        with self._create_submit_task() as submit_task:
            self._bill = self.model(
                name=title,
                description=body,
                author=author,
                pull_request=pull_request,
                status=Bill.Status.OPEN,
                constitutional=bool(is_constitutional(diff_text)),
                _submit_task=submit_task,
            )
            self._bill.full_clean()
            self._bill.save()
            logger.info("PR %s: Bill %s created", pull_request.number, self._bill.id)
            bill = self._bill

        return bill  # noqa: RET504

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
            logger.info(
                "PR %s: Scheduled %s",
                self._bill.pull_request.number,
                submit_task.name,
            )

            del self._bill


class Bill(TimeStampedModel):
    """Model for a proposal to merge a particular pull request into the main branch"""

    # Display info
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    # Users should be anonymized, not deleted
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    pull_request = models.ForeignKey(PullRequest, on_delete=models.PROTECT)

    class Status(models.TextChoices):
        """The possible statuses for a bill

        :meta private:"""

        OPEN = "open", _("Open")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")
        FAILED = "failed", _("Not Enough Votes")  # Failed to reach quorum
        # Translators: PR is short for "pull request"
        CLOSED = "closed", _("PR Closed")  # PR closed on Github

    #:
    status = models.CharField(
        max_length=10,
        default=Status.OPEN,
        choices=Status,
        help_text=_("The current status of the bill"),
    )
    constitutional = models.BooleanField(
        default=False,
        help_text=_("True if this bill is an amendment to the constitution"),
    )

    # Automatic fields
    votes = models.ManyToManyField(User, through=Vote, related_name="votes", blank=True)
    _submit_task = models.OneToOneField(PeriodicTask, on_delete=models.PROTECT)

    history = HistoricalRecords()

    objects = BillManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("pull_request",),
                # Can't reference Bill.Status because Bill isn't defined yet
                condition=models.Q(status="open"),
                name="unique_open_pull_request",
                violation_error_message=_(
                    "A Bill for this pull request is already open"
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"Bill {self.id}: {self.name} ({self.pull_request})"

    def get_absolute_url(self) -> str:
        """Returns URL to view this Bill instance"""
        return reverse("webiscite:bill-detail", kwargs={"pk": self.id})

    def get_update_url(self) -> str:
        """Returns URL to update this Bill instance"""
        return reverse("webiscite:bill-update", kwargs={"pk": self.id})

    def get_vote_url(self) -> str:
        """Returns URL for the current user to vote on this Bill instance"""
        return reverse("webiscite:bill-vote", kwargs={"pk": self.id})

    @property
    def yes_votes(self) -> models.QuerySet[User]:
        return self.votes.filter(vote__support=True)

    @property
    def no_votes(self) -> models.QuerySet[User]:
        return self.votes.filter(vote__support=False)

    def vote(self, user: User, *, support: bool) -> None:
        """Sets the given user's vote based on the support parameter

        If the user already voted the way the method would set, their vote is
        removed from the bill (i.e. if ``user`` is in ``bill.yes_votes`` and support is
        ``True``, ``user`` is removed from ``bill.yes_votes``)

        Args:
            user (User): The user voting on the bill
            support (bool): Whether the user supports the bill

        Raises:
            ClosedBillVoteError: If the bill is not open for voting
        """
        if self.status != self.Status.OPEN:
            raise ClosedBillVoteError("Bill is not open for voting")

        try:
            vote: Vote = self.vote_set.get(user=user)
            if vote.support == support:
                vote.delete()
                logger.info(
                    'PR %s: User %s retracted their vote "%s" on bill %s',
                    self.pull_request.number,
                    user.username,
                    "yes" if support else "no",
                    self.id,
                )

            else:
                vote.support = support
                vote.save(update_fields=["support", "when"])  # Ensure "when" is updated
                logger.info(
                    "PR %s: User %s changed their vote on bill %s from %s to %s",
                    self.pull_request.number,
                    user.username,
                    self.id,
                    not support,
                    support,
                )

        except Vote.DoesNotExist:
            self.votes.add(user, through_defaults={"support": support})
            logger.info(
                "PR %s: User %s voted %s on bill %s",
                self.pull_request.number,
                user.username,
                "yes" if support else "no",
                self.id,
            )

    def user_supports(self, user: User) -> bool | None:
        """
        Returns whether the given user supports, opposes, or has not voted on this bill

        Args:
            user: The user to check

        Returns:
            True if the user supports the bill, False if they oppose it, and None if
            they have not voted
        """
        try:
            vote: Vote = self.vote_set.get(user=user)
        except Vote.DoesNotExist:
            return None
        else:
            return vote.support

    def close(self) -> None:
        """Close the bill and disable its submit task"""
        self.status = self.Status.CLOSED
        self.save()
        logger.info("Bill %s set to closed", self.id)

        self._submit_task.enabled = False
        self._submit_task.save()
        logger.info("Submit task for bill %s disabled", self.id)

    def submit(self) -> None:
        """Check if the bill has enough votes to pass and update the status"""
        # Bill was closed before voting period ended
        if self.status != Bill.Status.OPEN:
            logger.info(
                "PR %s: bill %s was not open when submitted",
                self.pull_request.number,
                self.id,
            )
            return

        self.status = self._check_approval()
        self.save()

    def _check_approval(self) -> "Bill.Status":
        total_votes = self.votes.count()
        if total_votes < settings.WEBISCITE_MINIMUM_QUORUM:
            logger.info(
                "PR %s: bill %s rejected due to insufficient votes",
                self.pull_request.number,
                self.id,
            )
            return self.Status.FAILED

        approval = self.yes_votes.count() / total_votes
        if self.constitutional:
            approved = approval > settings.WEBISCITE_SUPERMAJORITY
        else:
            approved = approval > settings.WEBISCITE_NORMAL_MAJORITY

        if not approved:
            logger.info(
                "PR %s: bill %s rejected with %s%% approval",
                self.pull_request.number,
                self.id,
                approval * 100,
            )
            return self.Status.REJECTED

        logger.info(
            "PR %s: bill %s approved with %s%% approval",
            self.pull_request.number,
            self.id,
            approval,
        )
        return self.Status.APPROVED
