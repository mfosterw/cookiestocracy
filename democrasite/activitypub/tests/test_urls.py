from django.urls import resolve
from django.urls import reverse

from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person


def test_list():
    assert reverse("activitypub:note-list") == "/activitypub/notes/"
    assert resolve("/activitypub/notes/").view_name == "activitypub:note-list"


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


def test_note_like(note: Note):
    assert (
        reverse("activitypub:note-like", kwargs={"pk": note.id})
        == f"/activitypub/notes/{note.id}/like/"
    )
    assert (
        resolve(f"/activitypub/notes/{note.id}/like/").view_name
        == "activitypub:note-like"
    )


def test_note_repost(note: Note):
    assert (
        reverse("activitypub:note-repost", kwargs={"pk": note.id})
        == f"/activitypub/notes/{note.id}/repost/"
    )
    assert (
        resolve(f"/activitypub/notes/{note.id}/repost/").view_name
        == "activitypub:note-repost"
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


def test_following():
    assert reverse("activitypub:following-notes") == "/activitypub/person/following/"
    assert (
        resolve("/activitypub/person/following/").view_name
        == "activitypub:following-notes"
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


def test_follow(person: Person):
    assert (
        reverse("activitypub:person-follow", kwargs={"username": person.display_name})
        == f"/activitypub/person/{person.display_name}/follow/"
    )
    assert (
        resolve(f"/activitypub/person/{person.display_name}/follow/").view_name
        == "activitypub:person-follow"
    )
