from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from mptt.models import MPTTModel
from mptt.models import TreeForeignKey

User = get_user_model()


class PersonManager(models.Manager):
    """Manager for Person model with user prefetched."""

    def get_queryset(self):
        return super().get_queryset().select_related("user")


class Person(models.Model):  # type: ignore[django-manager-missing] # Issue caused by mptt
    """A person in the ActivityPub network, linked to a Django User."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    private_key = models.TextField()
    public_key = models.TextField()
    following = models.ManyToManyField(
        "self",
        related_name="followers",
        symmetrical=False,
        blank=True,
        help_text=_("People this person is following"),
    )

    objects = PersonManager()

    class Meta:
        verbose_name_plural = "People"

    def __str__(self):
        return f"Person: {self.user.username}"


class Note(TimeStampedModel, MPTTModel):  # type: ignore[django-manager-missing] # Issue caused by mptt
    """A note in the ActivityPub network, representing a short piece of content."""

    author = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="notes")
    content = models.TextField()
    in_reply_to = TreeForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="replies",
        blank=True,
        null=True,
    )

    class MPTTMeta:
        order_insertion_by = ["created"]
        parent_attr = "in_reply_to"

    def __str__(self):
        preview_length = 10
        return (
            f"{self.author.user.username}: {self.content[:preview_length]}"
            f"{'...' if len(self.content) > preview_length else ''}"
        )

    def get_absolute_url(self):
        """Get the URL for the note's detail view.

        Returns:
            str: URL for the note detail.
        """
        return reverse("activitypub:note-detail", kwargs={"pk": self.pk})

    def get_display_replies(self, max_depth=5) -> models.QuerySet:
        """Get direct replies and their leftmost descendant up to a specified depth.

        Args:
            max_depth (int, optional): The maximum depth to retrieve replies to children
            for, including the child level. Defaults to 5.

        Returns:
            models.QuerySet: A queryset of the relevant replies.
        """
        q = models.Q(level__lt=self.level + max_depth) & (
            models.Q(in_reply_to=self) | models.Q(lft__isnull=True)
        )
        return self.get_descendants().filter(q)
