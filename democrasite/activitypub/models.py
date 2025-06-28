from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from mptt.models import MPTTModel
from mptt.models import TreeForeignKey
from mptt.models import TreeManager

User = get_user_model()


class PersonManager(models.Manager):
    """Manager for Person model with user prefetched."""

    def get_queryset(self):
        return super().get_queryset().select_related("user")


class Person(TimeStampedModel):  # type: ignore[django-manager-missing] # Issue caused by mptt
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
    bio = models.TextField(
        blank=True,
        help_text=_("A short biography or description of the person"),
    )

    objects = PersonManager()

    class Meta:
        verbose_name_plural = "People"

    def __str__(self):
        return f"Person: {self.user.username}"

    @property
    def display_name(self):
        """Get the display name for the person.

        Returns:
            str: The username of the person.
        """
        return self.user.username

    def get_absolute_url(self):
        """Get the URL for the person's detail view.

        Returns:
            str: URL for the person detail.
        """
        return reverse(
            "activitypub:person-detail", kwargs={"username": self.display_name}
        )


class Like(models.Model):
    """A model to represent a like on a Note by a Person."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    note = models.ForeignKey("Note", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("person", "note")
        ordering = ["-created"]

    def __str__(self):
        return f'{self.person.display_name} liked "{self.note}"'


class Repost(models.Model):
    """A model to represent a repost of a Note by a Person."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    note = models.ForeignKey("Note", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("person", "note")
        ordering = ["-created"]

    def __str__(self):
        return f'{self.person.display_name} reposted "{self.note}"'


class NoteManager[T](TreeManager):
    def get_queryset(self) -> models.QuerySet[T]:
        """Get the queryset for notes, ordered by creation date."""
        return super().get_queryset().order_by(*self.model._meta.ordering)  # noqa: SLF001

    def get_person_notes(self, person: Person) -> models.QuerySet[T]:
        """Get notes for display on a person's profile page.

        This method returns all notes authored by the person as well as all their
        reposts, ordered by their creation or repost time. Reposts are annotated with
        the `reposted_by` and `reposted_at` fields for use in templates. If a user has
        reposted their own note, both the original note and the repost will be included
        in the results.

        Args:
            person (Person): The person whose notes and reposts are to be retrieved.

        Returns:
            models.QuerySet[T]: A queryset of notes and reposts ordered by time.
        """
        reposts = (
            person.reposts.annotate(reposted_by=models.Value(person.display_name))
            .annotate(reposted_at=models.F("repost__created"))
            .annotate(order_time=models.F("reposted_at"))
        )

        return (
            person.notes.annotate(
                reposted_by=models.Value(None, output_field=models.TextField())
            )
            .annotate(
                reposted_at=models.Value(None, output_field=models.DateTimeField())
            )
            .annotate(order_time=models.F("created"))
            .union(reposts)
            .order_by("-order_time")
        )


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
    likes = models.ManyToManyField(
        Person, through=Like, related_name="likes", blank=True
    )
    reposts = models.ManyToManyField(
        Person, through=Repost, related_name="reposts", blank=True
    )

    objects = NoteManager()

    class MPTTMeta:
        order_insertion_by = ["created"]
        parent_attr = "in_reply_to"

    class Meta:
        # TODO: determine why queryset ordering is not being applied
        ordering = ["-created"]

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

    def liked_by(self, person: Person) -> bool:
        """Check if a person has liked the note.

        Args:
            person (Person): The person to check for a like.
        Returns:
            bool: True if the person has liked the note, False otherwise.
        """
        return self.likes.filter(id=person.id).exists()

    def like(self, person: Person) -> bool:
        """Toggle a like on the note for a person.

        Args:
            person (Person): The person liking or unliking the note.
        Returns:
            bool: True if the like was added, False if it was removed.
        """
        if self.liked_by(person):
            self.likes.remove(person)
            return False
        self.likes.add(person)
        return True

    def reposted_by(self, person: Person) -> bool:
        """Check if a person has reposted the note.

        Args:
            person (Person): The person to check for a repost.
        Returns:
            bool: True if the person has reposted the note, False otherwise.
        """
        return self.reposts.filter(id=person.id).exists()

    def repost(self, person: Person) -> bool:
        """Toggle a repost on the note for a person.

        Args:
            person (Person): The person reposting or un-reposting the note.
        Returns:
            bool: True if the repost was added, False if it was removed.
        """
        if self.reposted_by(person):
            self.reposts.remove(person)
            return False
        self.reposts.add(person)
        return True
