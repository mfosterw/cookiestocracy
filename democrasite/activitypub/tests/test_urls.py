from django.urls import resolve
from django.urls import reverse

from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person


def test_list():
    assert reverse("activitypub:note-list") == "/activitypub/notes/"
    assert resolve("/activitypub/notes/").view_name == "activitypub:note-list"


def test_following():
    assert reverse("activitypub:following-notes") == "/activitypub/notes/following/"
    assert (
        resolve("/activitypub/notes/following/").view_name
        == "activitypub:following-notes"
    )


def test_create():
    assert reverse("activitypub:note-create") == "/activitypub/notes/create/"
    assert resolve("/activitypub/notes/create/").view_name == "activitypub:note-create"


def test_note_detail(note: Note):
    assert (
        reverse("activitypub:note-detail", kwargs={"pk": note.id})
        == f"/activitypub/notes/{note.id}/"
    )
    assert (
        resolve(f"/activitypub/notes/{note.id}/").view_name == "activitypub:note-detail"
    )


def test_note_reply(note: Note):
    assert (
        reverse("activitypub:note-reply", kwargs={"pk": note.id})
        == f"/activitypub/notes/{note.id}/reply/"
    )
    assert (
        resolve(f"/activitypub/notes/{note.id}/reply/").view_name
        == "activitypub:note-reply"
    )


def test_person_create():
    assert reverse("activitypub:person-create") == "/activitypub/person/create/"
    assert (
        resolve("/activitypub/person/create/").view_name == "activitypub:person-create"
    )


def test_person_update():
    assert reverse("activitypub:person-update") == "/activitypub/person/update/"
    assert (
        resolve("/activitypub/person/update/").view_name == "activitypub:person-update"
    )


def test_person_detail(person: Person):
    assert (
        reverse("activitypub:person-detail", kwargs={"username": person.display_name})
        == f"/activitypub/person/{person.display_name}/"
    )
    assert (
        resolve(f"/activitypub/person/{person.display_name}/").view_name
        == "activitypub:person-detail"
    )
