"""Models for the webiscite app"""

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_stubs_ext.db.models import TypedModelMeta

User = get_user_model()


class Vote(models.Model):
    """
    A vote for or against a bill, with a timestamp
    """

    bill = models.ForeignKey("Bill", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    support = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta(TypedModelMeta):
        indexes = [models.Index(fields=["bill", "user"])]
        get_latest_by = "timestamp"

    def __str__(self) -> str:
        return f"{self.user} {'for' if self.support else 'against'} {self.bill}"


class Bill(models.Model):
    """
    The model representing pull requests that users can vote for or against onsite
    """

    # Display info
    name = models.CharField(max_length=100)
    description = models.TextField()
    # Github info
    pr_num = models.IntegerField(_("Pull request number"))
    # Users should be anonymized, not deleted
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    additions = models.IntegerField(help_text=_("Lines added"))
    deletions = models.IntegerField(help_text=_("Lines removed"))
    sha = models.CharField(max_length=40, help_text=_("Unique identifier of PR commit"))

    # Backend info
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
        help_text=_("True iff this bill is an amendment to the constitution"),
    )

    # Automatic fields
    prop_date = models.DateTimeField(_("date proposed"), auto_now_add=True)
    votes = models.ManyToManyField(User, through=Vote, related_name="votes", blank=True)

    def __str__(self) -> str:
        return f"{self.name} (PR #{self.pr_num})"

    def get_absolute_url(self) -> str:
        """
        Returns URL to view this Bill instance
        """
        return reverse("webiscite:bill-detail", kwargs={"pk": self.id})

    def vote(self, support: bool, user: Any):
        """Sets the given user's vote based on the support parameter

        If the user already voted the way the method would set, their vote is
        removed from the bill (i.e. if user is in bill.yes_votes and support is
        True, user is removed from bill.yes_votes)
        """
        assert self.state == self.States.OPEN, "Only open bills may be voted on"

        try:
            vote = Vote.objects.get(bill=self, user=user)
            if vote.support == support:
                vote.delete()
                return
            vote.support = support
            vote.save()

        except Vote.DoesNotExist:
            # Stubs issue fixed (by me!) in https://github.com/typeddjango/django-stubs/pull/1943
            # Just waiting for new version to be released
            self.votes.add(user, through_defaults={"support": support})  # type: ignore[call-arg]

    @property
    def yes_votes(self) -> models.QuerySet[AbstractBaseUser]:
        return self.votes.filter(vote__support=True).all()  # pylint: disable=no-member

    @property
    def no_votes(self) -> models.QuerySet[AbstractBaseUser]:
        return self.votes.filter(vote__support=False).all()  # pylint: disable=no-member
