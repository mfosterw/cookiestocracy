from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from mptt.models import MPTTModel
from mptt.models import TreeForeignKey
from mptt.models import TreeManager
from simple_history import register
from simple_history.models import HistoricalRecords

User = get_user_model()


class Follow(models.Model):
    """Timestamped record of a person following another"""

    following = models.ForeignKey(
        "Person",
        on_delete=models.CASCADE,
        # "person1.follower_set" will contain all of the Follow objects of people
        # following person1. It is confusing when defining but makes much more sense
        # when accessing imo. See tests for an example.
        related_name="follower_set",
    )
    follower = models.ForeignKey(
        "Person", on_delete=models.CASCADE, related_name="following_set"
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("following", "follower"),
                name="unique_follow",
                violation_error_code=_("Can't follow a person more than once"),
            )  # type: ignore[call-overload]
        ]

    def __str__(self):
        return f"{self.follower} followed {self.following} on {self.created}"


class PersonManager(models.Manager):
    """Manager for Person model with user prefetched."""

    def get_queryset(self):
        return super().get_queryset().select_related("user")


class Person(TimeStampedModel):
    """A person in the ActivityPub network, linked to a Django User."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    private_key = models.TextField()
    public_key = models.TextField()
    bio = models.TextField(
        blank=True,
        help_text=_("A short biography or description of the person"),
    )
    following = models.ManyToManyField(
        "self",
        related_name="followers",
        symmetrical=False,
        through=Follow,
        through_fields=("follower", "following"),
        blank=True,
        help_text=_("People this person is following"),
    )

    history = HistoricalRecords(m2m_fields=[following])

    objects = PersonManager()

    class Meta:
        verbose_name_plural = _("People")

    def __str__(self):
        return self.display_name

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

    def get_follow_url(self):
        return reverse(
            "activitypub:person-follow", kwargs={"username": self.display_name}
        )

    def is_following(self, person: "Person") -> bool:
        """Check if a person is following this person.

        Args:
            person (Person): The person to check for a follow.
        Returns:
            bool: True if the person is following this person, False otherwise.
        """
        return self.following.filter(id=person.id).exists()

    def follow(self, person: "Person") -> bool:
        """Toggle whether this person follows another person.

        Args:
            person (Person): The person following or unfollowing this person.
        Returns:
            bool: True if the follow was added, False if it was removed.
        """
        if self.is_following(person):
            self.following.remove(person)
            return False
        self.following.add(person)
        return True


class Like(models.Model):
    """A model to represent a like on a Note by a Person."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    note = models.ForeignKey("Note", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("person", "note")
        ordering = ["-created"]

    def __str__(self):
        return f'{self.person} liked "{self.note}"'


class Repost(models.Model):
    """A model to represent a repost of a Note by a Person."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    note = models.ForeignKey("Note", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("person", "note")
        ordering = ["-created"]

    def __str__(self):
        return f'{self.person} reposted "{self.note}"'


class NoteManager(TreeManager):
    def get_queryset(self) -> models.QuerySet:
        """Get the queryset for notes, ordered by creation date."""
        return super().get_queryset().order_by(*self.model._meta.ordering)  # noqa: SLF001

    def get_person_notes(self, person: Person) -> models.QuerySet:
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
        reposts = person.reposts.annotate(
            repost_person=models.Value(person.display_name),
            repost_time=models.F("repost__created"),
            order_time=models.F("repost_time"),
        )

        posts = person.notes.annotate(
            repost_person=models.Value(None, output_field=models.TextField()),
            repost_time=models.Value(None, output_field=models.DateTimeField()),
            order_time=models.F("created"),
        )
        return posts.union(reposts).order_by("-order_time")

    def get_person_following_notes(self, person: Person) -> models.QuerySet:
        """Get notes from people the person is following.

        This method retrieves all notes authored or reposted by people that the
        specified person is following, ordered by the creation or repost time of the
        notes. This method removes duplicate notes.

        Args:
            person (Person): The person whose following notes are to be retrieved.

        Returns:
            models.QuerySet[T]: A queryset of notes and reposts from followed persons,
            ordered by time.
        """
        following = person.following.all()

        reposts = (  # Get most recent repost from followed persons for each note
            self.model.reposts.through.objects.filter(person__in=following)
            .order_by("note_id", "-created")
            .values("pk")
            .distinct()
        )

        repost_notes = self.filter(repost__in=reposts).order_by()

        posts = (
            self.filter(author__in=following)
            # TODO: this is probably very inefficient
            .exclude(pk__in=repost_notes.values("pk"))
            .annotate(
                repost_person=models.Value(None, output_field=models.TextField()),
                repost_time=models.Value(None, output_field=models.DateTimeField()),
                order_time=models.F("created"),
            )
            .order_by()  # clear default ordering
        )

        repost_notes = repost_notes.annotate(
            repost_person=models.F("repost__person__user__username"),
            repost_time=models.F("repost__created"),
            order_time=models.F("repost_time"),
        )

        return repost_notes.union(posts).order_by("-order_time")


class Note(TimeStampedModel, MPTTModel):
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

    def get_like_url(self):
        return reverse("activitypub:note-like", kwargs={"pk": self.id})

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

    def get_repost_url(self):
        return reverse("activitypub:note-repost", kwargs={"pk": self.id})

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


# HistoricalRecords field doesn't work on MPTT models (see https://github.com/django-commons/django-simple-history/issues/87)
register(Note, m2m_fields=["likes", "reposts"])
