from django.urls import resolve
from django.urls import reverse

from democrasite.social.models import Note
from democrasite.social.models import Person


def test_list():
    assert reverse("social:note-list") == "/social/notes/"
    assert resolve("/social/notes/").view_name == "social:note-list"


def test_create():
    assert reverse("social:note-create") == "/social/notes/create/"
    assert resolve("/social/notes/create/").view_name == "social:note-create"


def test_note_detail(note: Note):
    assert (
        reverse("social:note-detail", kwargs={"pk": note.id})
        == f"/social/notes/{note.id}/"
    )
    assert resolve(f"/social/notes/{note.id}/").view_name == "social:note-detail"


def test_note_reply(note: Note):
    assert (
        reverse("social:note-reply", kwargs={"pk": note.id})
        == f"/social/notes/{note.id}/reply/"
    )
    assert resolve(f"/social/notes/{note.id}/reply/").view_name == "social:note-reply"


def test_note_like(note: Note):
    assert (
        reverse("social:note-like", kwargs={"pk": note.id})
        == f"/social/notes/{note.id}/like/"
    )
    assert resolve(f"/social/notes/{note.id}/like/").view_name == "social:note-like"


def test_note_repost(note: Note):
    assert (
        reverse("social:note-repost", kwargs={"pk": note.id})
        == f"/social/notes/{note.id}/repost/"
    )
    assert resolve(f"/social/notes/{note.id}/repost/").view_name == "social:note-repost"


def test_person_create():
    assert reverse("social:person-create") == "/social/person/create/"
    assert resolve("/social/person/create/").view_name == "social:person-create"


def test_person_update():
    assert reverse("social:person-update") == "/social/person/update/"
    assert resolve("/social/person/update/").view_name == "social:person-update"


def test_following():
    assert reverse("social:following-notes") == "/social/person/following/"
    assert resolve("/social/person/following/").view_name == "social:following-notes"


def test_person_detail(person: Person):
    assert (
        reverse("social:person-detail", kwargs={"username": person.display_name})
        == f"/social/person/{person.display_name}/"
    )
    assert (
        resolve(f"/social/person/{person.display_name}/").view_name
        == "social:person-detail"
    )


def test_follow(person: Person):
    assert (
        reverse("social:person-follow", kwargs={"username": person.display_name})
        == f"/social/person/{person.display_name}/follow/"
    )
    assert (
        resolve(f"/social/person/{person.display_name}/follow/").view_name
        == "social:person-follow"
    )
