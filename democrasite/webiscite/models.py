"""Models for the webiscite app"""

import json
from logging import getLogger
from typing import Any

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from . import constitution

User = get_user_model()
logger = getLogger(__name__)


class Vote(models.Model):
    """A vote for or against a bill, with a timestamp"""

    bill = models.ForeignKey("Bill", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    support = models.BooleanField()
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} {'for' if self.support else 'against'} {self.bill}"


class PullRequest(models.Model):
    """Local representation of a pull request on Github"""

    number = models.IntegerField(_("Pull request number"), primary_key=True)
    title = models.CharField(max_length=100)
    additions = models.IntegerField(help_text=_("Lines added"))
    deletions = models.IntegerField(help_text=_("Lines removed"))
    # diff_url = models.URLField(help_text=_("URL to the diff of the pull request"))
    # Store Github username of author even if they are not a user on the site
    author_name = models.CharField(max_length=100)
    state = models.CharField(
        max_length=6,
        choices=(("closed", _("Closed")), ("open", _("Open"))),
        help_text=_("State of the PR on Github"),
    )
    # Unique by defintion but added the constraint for clarity
    sha = models.CharField(max_length=40, unique=True, help_text=_("Unique identifier of PR commit"))
    time_created = models.DateTimeField(auto_now_add=True)
    time_updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"PR #{self.number}"

    @classmethod
    def create_from_pr(cls, pr: dict[str, Any]) -> "PullRequest":
        """Update or create a pull request from a parsed JSON object representing the pull request

        If the given pull request exists, update it based on the request, otherwise create a new pull request instance

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
                # "diff_url": pr["diff_url"],
                "author_name": pr["user"]["login"],
                "state": pr["state"],
                "sha": pr["head"]["sha"],
            },
        )
        logger.info(f"PR %s: Pull request {'created' if created else 'updated'}", pr["number"])
        return pull_request

    def close(self) -> "Bill | None":
        """Close a pull request and update the local representation

        Args:
            pr_num: The number of the pull request to close

        Returns:
            The bill associated with the pull request, if it was open
        """
        self.state = "closed"
        self.save()

        try:
            bill: Bill = self.bill_set.get(state=Bill.States.OPEN)
        except Bill.DoesNotExist:
            logger.info("PR %s: No open bill found", self.number)
            return None
        else:
            bill.close()
            return bill


class Bill(models.Model):
    """Model for a proposal to merge a particular pull request into the main branch"""

    # Display info
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    # Users should be anonymized, not deleted
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    pull_request = models.ForeignKey(PullRequest, on_delete=models.PROTECT)

    class States(models.TextChoices):
        OPEN = "o", _("Open")
        APPROVED = "a", _("Approved")
        REJECTED = "r", _("Rejected")
        FAILED = "f", _("Not Enough Votes")  # Failed to reach quorum
        # Translators: PR is short for "pull request"
        CLOSED = "c", _("PR Closed")  # PR closed on Github

    state = models.CharField(
        max_length=1,
        choices=States.choices,
        default=States.OPEN,
        help_text=_("The current status of the bill"),
    )
    constitutional = models.BooleanField(
        default=False,
        help_text=_("True if this bill is an amendment to the constitution"),
    )

    # Automatic fields
    votes = models.ManyToManyField(User, through=Vote, related_name="votes", blank=True)
    time_created = models.DateTimeField(auto_now_add=True)
    time_updated = models.DateTimeField(auto_now=True)
    submit_task = models.OneToOneField(PeriodicTask, on_delete=models.PROTECT, null=True, blank=True)

    # TODO: Add a custom manager with a queryset method to get open bills (get manager from queryset)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("pull_request",),
                # Can't reference Bill.States because Bill isn't defined yet
                condition=models.Q(state="o"),
                name="unique_open_pull_request",
                violation_error_message=_("A Bill for this pull request is already open"),
            ),
        ]

    def __str__(self) -> str:
        return f"Bill {self.id}: {self.name} ({self.pull_request})"

    def get_absolute_url(self) -> str:
        """Returns URL to view this Bill instance"""
        return reverse("webiscite:bill-detail", kwargs={"pk": self.id})

    @property
    def yes_votes(self) -> models.QuerySet[AbstractBaseUser]:
        return self.votes.filter(vote__support=True).all()  # pylint: disable=no-member

    @property
    def no_votes(self) -> models.QuerySet[AbstractBaseUser]:
        return self.votes.filter(vote__support=False).all()  # pylint: disable=no-member

    def vote(self, user: AbstractBaseUser, support: bool):
        """Sets the given user's vote based on the support parameter

        If the user already voted the way the method would set, their vote is
        removed from the bill (i.e. if ``user`` is in ``bill.yes_votes`` and support is
        ``True``, ``user`` is removed from ``bill.yes_votes``)
        """
        assert self.state == self.States.OPEN, "Only open bills may be voted on"

        try:
            vote = Vote.objects.get(bill=self, user=user)  # type: ignore
            if vote.support == support:
                vote.delete()
                return
            vote.support = support
            vote.save()

        except Vote.DoesNotExist:
            # Stubs issue fixed (by me!) in https://github.com/typeddjango/django-stubs/pull/1943
            # Just waiting for new version to be released
            self.votes.add(user, through_defaults={"support": support})  # type: ignore[arg-type,call-arg]

    @classmethod
    def create_from_pr(cls, pr: dict[str, Any]) -> "tuple[PullRequest, Bill | None]":
        """Create a :class:`~democrasite.webiscite.models.PullRequest` and, if the creator has an account,
        :class:`~democrasite.webiscite.models.Bill` instance from a pull request

        Args:
            pr: The parsed JSON object representing the pull request

        Returns:
            A tuple containing the new or update pull request and new bill instance, if applicable
        """
        # It was very difficult to decide where to define this logic, but this seems like the best place
        pull_request = PullRequest.create_from_pr(pr)

        try:
            bill_kwargs = cls._extract_bill_args(pr, pull_request)
        except User.DoesNotExist:
            # If the creator of the pull request does not have a linked account,
            # a Bill cannot be created and the pr is ignored.
            logger.warning("PR %s: No bill created (user does not exist)", pr["number"])
            return pull_request, None

        # TODO: everything below here could be in BillManager
        bill = Bill(**bill_kwargs)
        bill.full_clean()
        bill.save()
        logger.info("PR %s: Bill %s created", pr["number"], bill.id)

        bill._schedule_submit()

        return pull_request, bill

    @staticmethod
    def _extract_bill_args(pr: dict[str, Any], pull_request: PullRequest) -> dict[str, Any]:
        """Extract relevant information from a pull request for creating a :class:`~democrasite.webiscite.models.Bill`

        Args:
            pr: The parsed JSON object representing the pull request

        Returns:
            A dictionary containing the relevant information
        """
        author = User.objects.filter(socialaccount__provider="github").get(socialaccount__uid=pr["user"]["id"])

        diff = requests.get(pr["diff_url"], timeout=10).text
        constitutional = bool(constitution.is_constitutional(diff))

        return {
            "name": pr["title"],
            "description": pr["body"] or "",
            "author": author,
            "pull_request": pull_request,
            "state": Bill.States.OPEN,
            "constitutional": constitutional,
        }

    def _schedule_submit(self) -> PeriodicTask:
        """Schedule a task to submit this bill for voting

        Returns:
            The task that was scheduled
        """
        # This can be extracted to a signal if we want to support other ways of creating bills
        voting_ends, _ = IntervalSchedule.objects.get_or_create(
            every=settings.WEBISCITE_VOTING_PERIOD, period=IntervalSchedule.DAYS
        )

        submit_bill = PeriodicTask.objects.create(
            interval=voting_ends,
            name=f"bill_submit:{self.id}",
            task="democrasite.webiscite.tasks.submit_bill",
            args=json.dumps([self.id]),
            one_off=True,
        )
        self.submit_task = submit_bill
        self.save()
        logger.info("PR %s: Scheduled %s", self.pull_request.number, submit_bill.name)
        return submit_bill

    def close(self) -> None:
        """Close the bill and disable its submit task"""
        self.state = self.States.CLOSED
        self.save()
        logger.info("Bill %s set to closed", self.id)

        submit_bill = PeriodicTask.objects.get(bill=self)
        submit_bill.enabled = False
        submit_bill.save()
        logger.info("Submit task for bill %s disabled", self.id)
