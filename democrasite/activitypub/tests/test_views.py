import json
from http import HTTPStatus

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse

from democrasite.activitypub import views
from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person
from democrasite.users.models import User

from .factories import NoteFactory
from .factories import PersonFactory


class TestNoteListView:
    def test_queryset(self, client: Client):
        batch_size = 3
        NoteFactory.create_batch(batch_size)

        response = client.get(reverse("activitypub:note-list"))
        notes = response.context["object_list"]
        assert len(notes) == batch_size
        for i in range(1, batch_size):
            assert notes[i - 1].created > notes[i].created, (
                "Notes should be sorted descending"
            )


class TestUserProfileMixin:
    def dummy_get_response(self, request: HttpRequest):
        pass

    def test_no_auth(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)
        request.user = AnonymousUser()

        view = views.UserProfileMixin()
        view.request = request

        response = view.dispatch(request)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("activitypub:note-list")

        messages_sent = [m.message for m in get_messages(request)]
        assert messages_sent == [
            "You must have an ActivityPub profile to access this page."
        ]

    def test_no_person(self, rf: RequestFactory, user: User):
        request = rf.get("/fake-url/")

        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)
        request.user = user

        view = views.UserProfileMixin()
        view.request = request

        response = view.dispatch(request)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("activitypub:note-list")

        messages_sent = [m.message for m in get_messages(request)]
        assert messages_sent == [
            "You must have an ActivityPub profile to access this page."
        ]

    def test_pass(self, person: Person, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = person.user

        view = views.UserProfileMixin()
        view.request = request

        # test_func passed, view will process
        with pytest.raises(
            AttributeError, match="'super' object has no attribute 'dispatch'"
        ):
            view.dispatch(request)


class TestRequirePersonDecorator:
    def test_no_auth(self, rf: RequestFactory):
        view = views.require_user_profile(lambda r: "Hi there")
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()

        response = view(request)

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_no_person(self, rf: RequestFactory, user: User):
        view = views.require_user_profile(lambda r: "Hi there")
        request = rf.get("/fake-url/")
        request.user = user

        response = view(request)

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_success(self, rf: RequestFactory, person: Person):
        view = views.require_user_profile(lambda r: "Hi there")
        request = rf.get("/fake-url/")
        request.user = person.user

        response = view(request)

        assert response == "Hi there"


class TestNoteDetailView:
    def test_view_response(self, note: Note, rf: RequestFactory):
        request = rf.get("/fake-url/")
        response = views.note_detail_view(request, pk=note.id)
        assert response.status_code == HTTPStatus.OK


class TestNoteCreateView:
    def test_get(self, person: Person, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = person.user
        response = views.note_create_view(request)
        assert response.status_code == HTTPStatus.OK

    def test_form_valid(self, person: Person, rf: RequestFactory):
        content = "This is a new note."
        request = rf.post("/fake-url/", {"content": content})
        request.user = person.user
        response = views.note_create_view(request)

        new_note = Note.objects.get(content=content)
        assert new_note.author == person
        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == new_note.get_absolute_url()


class TestNoteReplyView:
    def test_get(self, person: Person, note: Note, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = person.user
        response = views.note_reply_view(request, pk=note.pk)
        assert response.status_code == HTTPStatus.OK

    def test_form_valid(self, person: Person, note: Note, rf: RequestFactory):
        content = "This is a reply."
        request = rf.post("/fake-url/", {"content": content})
        request.user = person.user
        response = views.note_reply_view(request, pk=note.pk)

        reply_note = Note.objects.get(content=content)
        assert reply_note.author == person
        assert reply_note.in_reply_to == note
        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reply_note.get_absolute_url()


def test_note_like_view(note: Note, rf: RequestFactory):
    request = rf.post("/fake-url/")
    request.user = note.author.user

    response = views.note_like_view(request, note.id)

    assert note.author in note.likes.all()
    assert json.loads(response.content)["likes"] == 1


def test_note_repost_view(note: Note, rf: RequestFactory):
    request = rf.post("/fake-url/")
    request.user = note.author.user

    response = views.note_repost_view(request, note.id)

    assert note.author in note.reposts.all()
    assert json.loads(response.content)["reposts"] == 1


class TestPersonDetailView:
    def test_get_context_data(self, person: Person, rf: RequestFactory):
        batch_size = 3
        NoteFactory.create_batch(batch_size, author=person)
        view = views.PersonDetailView()
        request = rf.get("/fake-url/")

        request.user = person.user
        view.request = request
        view.object = person

        context = view.get_context_data()

        assert "note_list" in context
        assert len(context["note_list"]) == batch_size
        assert list(context["note_list"]) == list(
            person.notes.order_by("-created").all()
        )


class TestPersonCreateView:
    def dummy_get_response(self, request: HttpRequest):
        pass

    def test_unauthenticated(self, rf: RequestFactory):
        # Unauthenticated
        request = rf.post("/fake-url/")
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)
        request.user = AnonymousUser()

        response = views.person_create_view(request)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert (
            response.url
            == f"{reverse(settings.LOGIN_URL)}?next={reverse('activitypub:note-list')}"
        )

        messages_sent = [m.message for m in get_messages(request)]
        assert messages_sent == ["You must be logged in to do that."]

    def test_person_exists(self, rf: RequestFactory, person: Person):
        request = rf.post("/fake-url/")
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)
        request.user = person.user

        response = views.person_create_view(request)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert (
            response.url
            == f"{reverse('activitypub:person-detail', args=[person.display_name])}"
        )

        messages_sent = [m.message for m in get_messages(request)]
        assert messages_sent == ["You already have an ActivityPub Profile!"]

    def test_create_person(self, user: User, client: Client):
        assert not hasattr(user, "person")

        client.force_login(user)

        response = client.post(reverse("activitypub:person-create"))

        user.refresh_from_db()
        assert hasattr(user, "person")
        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == user.person.get_absolute_url()

        response = client.get(response.url)

        messages_sent = [m.message for m in response.context["messages"]]
        assert messages_sent == ["Profile created successfully."]


class TestPersonUpdateView:
    def test_get_object(self, person: Person, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = person.user
        view = views.PersonUpdateView()
        view.request = request

        obj = view.get_object()
        assert obj == person

    def test_update_person(self, person: Person, rf: RequestFactory):
        new_bio = "This is my new bio."
        request = rf.post("/fake-url/", {"bio": new_bio})
        request.user = person.user

        response = views.person_update_view(request, pk=person.pk)

        person.refresh_from_db()
        assert person.bio == new_bio
        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == person.get_absolute_url()


class TestPersonFollowingNotesView:
    def test_get_queryset(self, person: Person, rf: RequestFactory):
        person_followed = PersonFactory.create()
        person.follow(person_followed)

        note_from_followed = NoteFactory(author=person_followed)
        note_from_other = NoteFactory()

        request = rf.get("/fake-url/")
        request.user = person.user
        view = views.PersonFollowingNotesView()
        view.request = request

        queryset = view.get_queryset()
        assert queryset.count() == 1
        assert note_from_followed in queryset
        assert note_from_other not in queryset


def test_person_follow_view(person: Person, rf: RequestFactory):
    person2 = PersonFactory.create()
    request = rf.post("/fake-url/")
    request.user = person.user

    response = views.person_follow_view(request, person2.display_name)

    assert person in person2.followers.all()
    assert json.loads(response.content)["followers"] == 1
