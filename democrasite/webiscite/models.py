"""Models for the webiscite app"""

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Vote(models.Model):
    """
    A vote for or against a bill, with a timestamp
    """

    bill = models.ForeignKey("Bill", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    support = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} {'for' if self.support else 'against'} {self.bill}"


class PullRequest(models.Model):
    """
    Local representation of a pull request on Github
    """

    pr_num = models.IntegerField(_("Pull request number"), primary_key=True)
    title = models.CharField(max_length=100)
    # Store Github username of author even if they are not a user on the site
    author_name = models.CharField(max_length=100)
    state = models.CharField(
        max_length=6,
        choices=(("closed", _("Closed")), ("open", _("Open"))),
        help_text=_("State of the PR on Github"),
    )
    additions = models.IntegerField(help_text=_("Lines added"))
    deletions = models.IntegerField(help_text=_("Lines removed"))
    # Unique by defintion but added the constraint for clarity
    sha = models.CharField(max_length=40, unique=True, help_text=_("Unique identifier of PR commit"))
    prop_date = models.DateTimeField(_("date proposed"), auto_now_add=True)

    def __str__(self) -> str:
        return f"PR #{self.pr_num}"


class BillManager(models.Manager["Bill"]):
    def create(self, **kwargs: Any) -> "Bill":
        if not isinstance(kwargs["author"], User):
            kwargs["author"] = User.objects.filter(socialaccount__provider="github").get(
                socialaccount__uid=kwargs["author"]
            )

        bill = Bill(**kwargs)
        bill.full_clean()
        bill.save()

        return bill


class Bill(models.Model):
    """
    Model for a proposal to merge a particular pull request into the main branch
    """

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
    prop_date = models.DateTimeField(_("date proposed"), auto_now_add=True)
    votes = models.ManyToManyField(User, through=Vote, related_name="votes", blank=True)

    objects = BillManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("pull_request",),
                # Can't reference Bill.States because Bill isn't defined yet
                condition=models.Q(state="o"),
                name="unique_open_pull_request",
                violation_error_message=_("A Bill for this pull request is already open"),
            ),
            models.CheckConstraint(
                check=(models.Q(pull_request__state="open") | ~models.Q(state="o")),
                name="pull_request_state",
                violation_error_message=_("The pull request for this bill must be open for the bill to be open"),
            ),
        ]

    def __str__(self) -> str:
        return f"Bill {self.id}: {self.name} ({self.pull_request})"

    def get_absolute_url(self) -> str:
        """
        Returns URL to view this Bill instance
        """
        return reverse("webiscite:bill-detail", kwargs={"pk": self.id})

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

    @property
    def yes_votes(self) -> models.QuerySet[AbstractBaseUser]:
        return self.votes.filter(vote__support=True).all()  # pylint: disable=no-member

    @property
    def no_votes(self) -> models.QuerySet[AbstractBaseUser]:
        return self.votes.filter(vote__support=False).all()  # pylint: disable=no-member
