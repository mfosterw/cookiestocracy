from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person
from democrasite.users.models import User

from .factories import NoteFactory
from .factories import PersonFactory


class TestFollow:
    def test_str(self, person: Person):
        follower = PersonFactory.create()
        follower.follow(person)

        follow = follower.following_set.first()
        assert follow.following == person
        assert str(follow) == f"{follower} followed {person} on {follow.created}"


class TestPersonManager:
    def test_get_queryset(self, person: Person, django_assert_num_queries):
        # Should only be one query due to select_related("user")
        with django_assert_num_queries(1):
            p = Person.objects.get(id=person.id)
            assert p.user.username is not None


class TestPerson:
    def test_str(self, user: User):
        person = PersonFactory.create(user=user)
        assert str(person) == user.username

    def test_display_name(self, person: Person):
        assert person.display_name == person.user.username

    def test_get_absolute_url(self, person: Person):
        assert (
            person.get_absolute_url() == f"/activitypub/person/{person.user.username}/"
        )

    def test_get_follow_url(self, person: Person):
        assert (
            person.get_follow_url()
            == f"/activitypub/person/{person.user.username}/follow/"
        )

    def test_is_following(self, person: Person):
        person2 = PersonFactory.create()
        person.following.add(person2)
        assert person.is_following(person2)

    def test_follow(self, person: Person):
        person2 = PersonFactory.create()
        person.follow(person2)
        assert person2 in person.following.all()

        person.follow(person2)
        assert person2 not in person.following.all()


class TestLike:
    def test_str(self, note: Note, person: Person):
        note.like(person)

        assert str(note.like_set.first()) == f'{person.display_name} liked "{note!s}"'


class TestRepost:
    def test_str(self, note: Note, person: Person):
        note.repost(person)

        assert (
            str(note.repost_set.first()) == f'{person.display_name} reposted "{note!s}"'
        )


class TestNoteManager:
    def test_get_queryset(self):
        notes = NoteFactory.create_batch(5)
        # Test reversed sorting
        assert list(Note.objects.all()) == list(reversed(notes))

    def test_get_person_notes(self, person: Person, note: Note):
        notes = NoteFactory.create_batch(3, author=person)
        note.repost(person)
        notes[1].repost(person)
        notes[1].repost(note.author)  # shouldn't affect output

        person_notes = Note.objects.get_person_notes(person)
        # Use ids since the reposts get annotated in the function
        assert [note.id for note in person_notes] == [
            notes[1].id,  # reposts of own notes appear twice
            note.id,
            notes[2].id,
            notes[1].id,
            notes[0].id,
        ]

        repost = person_notes[1]
        assert repost.repost_person == person.display_name
        assert repost.repost_time == note.repost_set.first().created  # type: ignore[union-attr]

    def test_get_person_following_notes(self, person: Person):
        person2 = PersonFactory.create()
        notes = NoteFactory.create_batch(3, author=person2)
        own_notes = NoteFactory.create_batch(2, author=person)

        own_notes[0].repost(person2)
        notes[1].repost(person2)
        notes[1].repost(person)  # ensure returned repost_person is correct

        person.follow(person2)

        following_notes = Note.objects.get_person_following_notes(person)
        assert [note.id for note in following_notes] == [
            notes[1].id,
            own_notes[0].id,
            notes[2].id,
            notes[0].id,
        ]

        repost = following_notes[1]
        assert repost.repost_person == person2.display_name
        assert repost.repost_time == own_notes[0].repost_set.first().created  # type: ignore[union-attr]


class TestNote:
    def test_str_long_content(self):
        note = NoteFactory.create(content="a" * 20)
        assert str(note) == f"{note.author.user.username}: {'a' * 10}..."

    def test_str_short_content(self):
        note = NoteFactory.create(content="short")
        assert str(note) == f"{note.author.user.username}: short"

    def test_get_absolute_url(self, note: Note):
        assert note.get_absolute_url() == f"/activitypub/notes/{note.pk}/"

    def test_get_like_url(self, note: Note):
        assert note.get_like_url() == f"/activitypub/notes/{note.id}/like/"

    def test_liked_by(self, note: Note, person: Person):
        assert not note.liked_by(person)

        note.likes.add(person)

        assert note.liked_by(person)

    def test_like(self, note: Note, person: Person):
        note.like(person)

        assert person in note.likes.all()

        note.like(person)

        assert person not in note.likes.all()

    def test_get_repost_url(self, note: Note):
        assert note.get_repost_url() == f"/activitypub/notes/{note.id}/repost/"

    def test_reposted_by(self, note: Note, person: Person):
        assert not note.reposted_by(person)

        note.reposts.add(person)

        assert note.reposted_by(person)

    def test_repost(self, note: Note, person: Person):
        note.repost(person)

        assert person in note.reposts.all()

        note.repost(person)

        assert person not in note.reposts.all()
