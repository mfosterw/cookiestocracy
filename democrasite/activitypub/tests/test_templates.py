from http import HTTPStatus

from django.shortcuts import render
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse

from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person
from democrasite.activitypub.tests.factories import NoteFactory
from democrasite.users.models import User


class TestBaseTemplate:
    def test_base_no_person(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = user

        response = render(request, "activitypub/base.html")

        assert response.status_code == HTTPStatus.OK
        assert b"Create Profile" in response.content

    def test_base_with_person(self, person: Person, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = person.user

        response = render(request, "activitypub/base.html")

        assert b"Profile" in response.content


class TestNoteListTemplate:
    def test_no_notes(self, client: Client):
        response = client.get(reverse("activitypub:note-list"))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "activitypub/note_list.html"
        assert b"No notes available" in response.content

    def test_with_notes(self, note: Note, client: Client):
        NoteFactory.create(in_reply_to=note)

        content = client.get(reverse("activitypub:note-list")).content.decode()

        assert note.content in content
        assert "No notes available" not in content
        assert "In reply to: " in content

    def test_reply_link(self, note: Note, user: User, client: Client):
        content = client.get(reverse("activitypub:note-list")).content.decode()

        assert reverse("activitypub:note-reply", kwargs={"pk": note.id}) not in content

        client.force_login(user)

        content = client.get(reverse("activitypub:note-list")).content.decode()

        assert reverse("activitypub:note-reply", kwargs={"pk": note.id}) in content


class TestNoteDetailTemplate:
    def test_note_detail(self, note: Note, client: Client):
        response = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        )

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "activitypub/note_detail.html"
        assert note.content in response.content.decode()
        assert "No replies yet." in response.content.decode()

    def test_reply_link(self, note: Note, user: User, client: Client):
        client.force_login(user)

        content = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        ).content.decode()

        assert reverse("activitypub:note-reply", kwargs={"pk": note.id}) in content

    def test_note_replies(self, note: Note, client: Client):
        reply1 = NoteFactory.create(in_reply_to=note)
        reply2 = NoteFactory.create(in_reply_to=note)

        content = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        ).content.decode()

        assert reply1.content in content
        assert reply2.content in content
        assert "No replies yet." not in content

    def test_note_ancestors(self, note: Note, client: Client):
        reply = NoteFactory.create(in_reply_to=note)
        reply2 = NoteFactory.create(in_reply_to=reply)

        content = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": reply2.id})
        ).content.decode()

        assert note.content in content
        assert reply.content in content
        assert reply2.content in content


class TestNoteFormTemplate:
    def test_note_form(self, person: Person, client: Client):
        client.force_login(person.user)

        response = client.get(reverse("activitypub:note-create"))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "activitypub/note_form.html"
        assert b"Content" in response.content

    def test_note_reply_form(self, note: Note, person: Person, client: Client):
        client.force_login(person.user)

        response = client.get(reverse("activitypub:note-reply", kwargs={"pk": note.id}))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "activitypub/note_form.html"


class TestPersonDetailTemplate:
    def test_person_detail(self, person: Person, client: Client):
        response = client.get(
            reverse(
                "activitypub:person-detail", kwargs={"username": person.display_name}
            )
        )

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "activitypub/person_detail.html"
        assert person.display_name in response.content.decode()
        assert person.bio in response.content.decode()
        assert "This user hasn't posted anything yet." in response.content.decode()

    def test_person_notes(self, person: Person, client: Client):
        note = NoteFactory.create(author=person)
        reply = NoteFactory.create(author=person, in_reply_to=note)
        note2 = NoteFactory.create(author=person)
        bad_note = NoteFactory.create()

        content = client.get(
            reverse(
                "activitypub:person-detail", kwargs={"username": person.display_name}
            )
        ).content.decode()

        assert note.content in content
        assert reply.content in content
        assert note2.content in content
        assert bad_note.content not in content

    def test_logged_in(self, person: Person, client: Client):
        client.force_login(person.user)

        response = client.get(
            reverse(
                "activitypub:person-detail", kwargs={"username": person.display_name}
            )
        )

        assert response.status_code == HTTPStatus.OK
        assert b"svg" in response.content


class TestPersonFormTemplate:
    def test_person_update_form(self, person: Person, client: Client):
        client.force_login(person.user)

        response = client.get(reverse("activitypub:person-update"))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "activitypub/person_form.html"
        assert b"Bio" in response.content
