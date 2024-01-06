"""Models for the webiscite app"""

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Bill(models.Model):
    """
    The model representing pull requests that users can vote for or against onsite
    """

    # Display info
    name = models.CharField(max_length=100)
    description = models.TextField()
    # Github info
    pr_num = models.IntegerField(_("Pull request number"))
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    additions = models.IntegerField(help_text=_("Lines added"))
    deletions = models.IntegerField(help_text=_("Lines removed"))
    sha = models.CharField(max_length=40, help_text=_("Unique identifier of PR commit"))
    # Backend info
    OPEN = "o"
    APPROVED = "a"
    REJECTED = "r"
    FAILED = "f"  # Failed to reach quorum
    CLOSED = "c"  # PR closed on Github
    STATES = (
        (OPEN, _("Open")),
        (APPROVED, _("Approved")),
        (REJECTED, _("Rejected")),
        (FAILED, _("Not Enough Votes")),
        # Translators: PR is short for "pull request"
        (CLOSED, _("PR Closed")),
    )
    state = models.CharField(
        max_length=1,
        choices=STATES,
        default=OPEN,
        help_text=_("The current status of the bill"),
    )
    constitutional = models.BooleanField(
        default=False,
        help_text=_("True iff this bill is an amendment to the constitution"),
    )

    # Automatic fields
    prop_date = models.DateTimeField(_("date proposed"), auto_now_add=True)
    yes_votes: "models.ManyToManyField[AbstractBaseUser, Any]" = models.ManyToManyField(
        User, related_name="yes_votes", blank=True
    )
    no_votes: "models.ManyToManyField[AbstractBaseUser, Any]" = models.ManyToManyField(
        User, related_name="no_votes", blank=True
    )

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
        assert self.state == self.OPEN, "Only open bills may be voted on"

        if support:
            self.no_votes.remove(user)
            if self in user.yes_votes.all():
                self.yes_votes.remove(user)
            else:
                self.yes_votes.add(user)
        else:
            self.yes_votes.remove(user)
            if self in user.no_votes.all():
                self.no_votes.remove(user)
            else:
                self.no_votes.add(user)
