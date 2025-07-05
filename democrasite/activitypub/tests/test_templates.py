from http import HTTPStatus

from django.shortcuts import render
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse

from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person
from democrasite.activitypub.tests.factories import NoteFactory
from democrasite.activitypub.tests.factories import PersonFactory
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

    def test_reply_link(self, note: Note, user: User, person: Person, client: Client):
        content = client.get(reverse("activitypub:note-list")).content.decode()

        assert reverse("activitypub:note-reply", kwargs={"pk": note.id}) not in content

        client.force_login(user)

        content = client.get(reverse("activitypub:note-list")).content.decode()

        assert (
            reverse("activitypub:note-reply", kwargs={"pk": note.id}) not in content
        ), "Reply link should not be visible to users without a Person profile"

        client.force_login(person.user)

        content = client.get(reverse("activitypub:note-list")).content.decode()

        assert reverse("activitypub:note-reply", kwargs={"pk": note.id}) in content

    def test_reposted(self, note: Note, person: Person, client: Client):
        note.repost(person)

        content = client.get(
            reverse(
                "activitypub:person-detail", kwargs={"username": person.display_name}
            )
        ).content.decode()

        assert "Reposted by:" in content


class TestNoteDetailTemplate:
    def test_note_detail(self, note: Note, client: Client):
        response = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        )

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "activitypub/note_detail.html"
        assert note.content in response.content.decode()
        assert "No replies yet." in response.content.decode()

    def test_reply_link(self, note: Note, person: Person, client: Client):
        client.force_login(person.user)

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

    def test_like(self, note: Note, person: Person, client: Client):
        content = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        ).content.decode()

        assert "bi-heart" not in content

        client.force_login(person.user)

        content = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        ).content.decode()

        assert "bi-heart" in content
        assert "bi-heart-fill" not in content

        note.like(person)

        content = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        ).content.decode()

        assert "bi-heart-fill" in content

    def test_repost(self, note: Note, person: Person, client: Client):
        content = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        ).content.decode()

        assert "bi-repeat" not in content

        client.force_login(person.user)

        content = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        ).content.decode()

        assert "bi-repeat" in content
        assert "text-success" not in content

        note.repost(person)

        content = client.get(
            reverse("activitypub:note-detail", kwargs={"pk": note.id})
        ).content.decode()

        assert "text-success" in content


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
        assert (  # not logged in --> no follow button
            "Follow" not in response.content.decode()
        )

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

    def test_follow_button(self, person: Person, client: Client):
        person2 = PersonFactory.create()
        client.force_login(person2.user)

        content = client.get(
            reverse(
                "activitypub:person-detail", kwargs={"username": person.display_name}
            )
        ).content.decode()

        assert "Follow" in content  # this doesn't actually work as a check
        assert "person-unfollow" not in content
        assert (
            reverse(
                "activitypub:person-follow", kwargs={"username": person.display_name}
            )
            in content
        )

    def test_unfollow_button(self, person: Person, client: Client):
        person2 = PersonFactory.create()
        person2.follow(person)
        client.force_login(person2.user)

        content = client.get(
            reverse(
                "activitypub:person-detail", kwargs={"username": person.display_name}
            )
        ).content.decode()

        assert "person-unfollow" in content
        assert (
            reverse(
                "activitypub:person-follow", kwargs={"username": person.display_name}
            )
            in content
        )

    def test_edit_link(self, person: Person, client: Client):
        client.force_login(person.user)

        response = client.get(
            reverse(
                "activitypub:person-detail", kwargs={"username": person.display_name}
            )
        )

        assert response.status_code == HTTPStatus.OK
        assert reverse("activitypub:person-update") in response.content.decode()


class TestPersonFormTemplate:
    def test_person_update_form(self, person: Person, client: Client):
        client.force_login(person.user)

        response = client.get(reverse("activitypub:person-update"))

        assert response.status_code == HTTPStatus.OK
        assert response.templates[0].name == "activitypub/person_form.html"
        assert b"Bio" in response.content
