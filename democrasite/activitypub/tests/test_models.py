from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person
from democrasite.users.models import User

from .factories import NoteFactory
from .factories import PersonFactory


class TestPersonManager:
    def test_get_queryset(self, person: Person, django_assert_num_queries):
        # Should only be one query due to select_related("user")
        with django_assert_num_queries(1):
            p = Person.objects.get(id=person.id)
            assert p.user.username is not None


class TestPerson:
    def test_person_str(self, user: User):
        person = PersonFactory.create(user=user)
        assert str(person) == f"Person: {user.username}"

    def test_display_name(self, person: Person):
        assert person.display_name == person.user.username

    def test_get_absolute_url(self, person: Person):
        assert (
            person.get_absolute_url() == f"/activitypub/person/{person.user.username}/"
        )


class TestNote:
    def test_note_str_long_content(self):
        note = NoteFactory.create(content="a" * 20)
        assert str(note) == f"{note.author.user.username}: {'a' * 10}..."

    def test_note_str_short_content(self):
        note = NoteFactory.create(content="short")
        assert str(note) == f"{note.author.user.username}: short"

    def test_get_absolute_url(self, note: Note):
        assert note.get_absolute_url() == f"/activitypub/notes/{note.pk}/"
