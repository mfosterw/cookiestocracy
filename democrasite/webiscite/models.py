"""Models for the webiscite app"""

import json
from logging import getLogger
from typing import Any
from typing import Self
from typing import cast

import requests
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import IntervalSchedule
from django_celery_beat.models import PeriodicTask
from model_utils.models import StatusField
from model_utils.models import StatusModel
from model_utils.models import TimeStampedModel

from democrasite.users.models import User

from . import constitution

logger = getLogger(__name__)


class Vote(models.Model):
    """A vote for or against a bill, with a timestamp"""

    bill = models.ForeignKey("Bill", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    support = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    # Doesn't need modified time because it's always deleted and re-added

    def __str__(self) -> str:
        return f"{self.user} {'for' if self.support else 'against'} {self.bill}"


class PullRequest(StatusModel, TimeStampedModel):
    """Local representation of a pull request on Github"""

    number = models.IntegerField(_("Pull request number"), primary_key=True)
    title = models.CharField(max_length=100)
    additions = models.IntegerField(help_text=_("Lines added"))
    deletions = models.IntegerField(help_text=_("Lines removed"))
    diff_url = models.URLField(help_text=_("URL to the diff of the pull request"))
    # Store Github username of author even if they are not a user on the site
    author_name = models.CharField(max_length=100)
    #:
    STATUS = (("open", _("Open")), ("closed", _("Closed")))
    # Unique by defintion but added the constraint for clarity
    sha = models.CharField(
        max_length=40, unique=True, help_text=_("Unique identifier of PR commit")
    )

    def __str__(self) -> str:
        return f"PR #{self.number}"

    @classmethod
    def create_from_pr(cls, pr: dict[str, Any]) -> Self:
        """Update or create a pull request from a parsed JSON object representing the it

        If the given pull request exists, update it based on the request, otherwise
        create a new pull request instance

        Args:
            pr: The parsed JSON object representing the pull request

        Returns:
            The new PullRequest instance
        """
        pull_request, created = cls.objects.update_or_create(
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

        act = "created" if created else "updated"
        logger.info("PR %s: Pull request %s", pr["number"], act)

        return cast(Self, pull_request)  # mypy infers wrong type (Pylance doesn't 👀)

    def close(self) -> "Bill | None":
        """Close a pull request and update the local representation

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


class Bill(StatusModel, TimeStampedModel):
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

    #:-: The possible statuses for a bill. Use ``Bill.Status.VALUE`` to access.
    STATUS = Status.choices
    status = StatusField(
        max_length=10,
        default=Status.OPEN,
        help_text=_("The current status of the bill"),
    )
    constitutional = models.BooleanField(
        default=False,
        help_text=_("True if this bill is an amendment to the constitution"),
    )

    # Automatic fields
    votes = models.ManyToManyField(User, through=Vote, related_name="votes", blank=True)
    submit_task = models.OneToOneField(
        PeriodicTask, on_delete=models.PROTECT, null=True, blank=True
    )

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
        """
        assert self.status == self.Status.OPEN, "Only open bills may be voted on"

        try:
            vote: Vote = self.vote_set.get(user=user)
            if vote.support == support:
                vote.delete()
                return
            vote.support = support
            vote.save()

        except Vote.DoesNotExist:
            # Stubs issue fixed (by me!) in https://github.com/typeddjango/django-stubs/pull/1943
            # Just waiting for new version to be released
            self.votes.add(user, through_defaults={"support": support})  # type: ignore[call-arg]

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

    @classmethod
    def create_from_pr(cls, pr: dict[str, Any]) -> tuple[PullRequest, Self | None]:
        """Create a :class:`~democrasite.webiscite.models.PullRequest` and, if the
        creator has an account, :class:`~democrasite.webiscite.models.Bill` instance
        from a pull request

        Args:
            pr: The parsed JSON object representing the pull request

        Returns:
            A tuple containing the new or update pull request and new bill instance, if
            applicable
        """
        # It was very difficult to decide where to define this logic, but this seems
        # like the best place
        pull_request = PullRequest.create_from_pr(pr)

        try:
            bill_kwargs = cls._extract_bill_args(pr, pull_request)
        except User.DoesNotExist:
            # If the creator of the pull request does not have a linked account,
            # a Bill cannot be created and the pr is ignored.
            logger.warning("PR %s: No bill created (user does not exist)", pr["number"])
            return pull_request, None

        # TODO: everything below here could be in BillManager
        bill = cls(**bill_kwargs)
        bill.full_clean()
        bill.save()
        logger.info("PR %s: Bill %s created", pr["number"], bill.id)

        bill._schedule_submit()  # noqa: SLF001 # Apparently ruff can't tell this is the same type as self

        return pull_request, bill

    @staticmethod
    def _extract_bill_args(
        pr: dict[str, Any], pull_request: PullRequest
    ) -> dict[str, Any]:
        """Extract relevant information from a pull request for creating a
        :class:`~democrasite.webiscite.models.Bill`

        Args:
            pr: The parsed JSON object representing the pull request

        Returns:
            A dictionary containing the relevant information
        """
        author = User.objects.filter(socialaccount__provider="github").get(
            socialaccount__uid=pr["user"]["id"]
        )

        diff = requests.get(pr["diff_url"], timeout=10).text
        constitutional = bool(constitution.is_constitutional(diff))

        return {
            "name": pr["title"],
            "description": pr["body"] or "",
            "author": author,
            "pull_request": pull_request,
            "status": Bill.Status.OPEN,
            "constitutional": constitutional,
        }

    def _schedule_submit(self) -> PeriodicTask:
        """Schedule a task to submit this bill for voting

        Returns:
            The task that was scheduled
        """
        # This can be extracted to a signal if we want to support other creaton methods
        voting_ends, _ = IntervalSchedule.objects.get_or_create(
            every=settings.WEBISCITE_VOTING_PERIOD, period=IntervalSchedule.DAYS
        )

        submit_bill = PeriodicTask.objects.create(
            interval=voting_ends,
            name=f"bill_submit:{self.id}",
            task="democrasite.webiscite.tasks.submit_bill",
            args=json.dumps([self.id]),
            one_off=True,
            # If last_run_at is not set, the task will run relative to when the
            # scheduler started, not when it was created
            last_run_at=timezone.now(),
        )
        self.submit_task = submit_bill
        self.save()
        logger.info("PR %s: Scheduled %s", self.pull_request.number, submit_bill.name)
        return submit_bill

    def close(self) -> None:
        """Close the bill and disable its submit task"""
        self.status = self.Status.CLOSED
        self.save()
        logger.info("Bill %s set to closed", self.id)

        submit_bill = PeriodicTask.objects.get(bill=self)
        submit_bill.enabled = False
        submit_bill.save()
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
