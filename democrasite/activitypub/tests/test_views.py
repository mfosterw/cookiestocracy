from http import HTTPStatus

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse

from democrasite.activitypub import views
from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person
from democrasite.users.models import User

from .factories import NoteFactory
from .factories import PersonFactory


class TestNoteListView:
    def test_queryset(self):
        batch_size = 3
        NoteFactory.create_batch(batch_size)

        notes = views.NoteListView.queryset
        assert len(notes) == batch_size
        for i in range(1, batch_size):
            assert notes[i - 1].created > notes[i].created, (
                "Notes should be sorted descending"
            )


class TestUserProfileMixin:
    def test_no_auth(self, rf: RequestFactory):
        request = rf.get("/fake-url/")

        SessionMiddleware(lambda r: None).process_request(request)
        MessageMiddleware(lambda r: None).process_request(request)
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

        SessionMiddleware(lambda r: None).process_request(request)
        MessageMiddleware(lambda r: None).process_request(request)
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


class TestUserFollowingNotesView:
    def test_get_queryset(self, person: Person, rf: RequestFactory):
        person_followed = PersonFactory()
        person.following.add(person_followed)

        note_from_followed = NoteFactory(author=person_followed)
        note_from_other = NoteFactory()

        request = rf.get("/fake-url/")
        request.user = person.user
        view = views.UserFollowingNotesView()
        view.request = request

        queryset = view.get_queryset()
        assert queryset.count() == 1
        assert note_from_followed in queryset
        assert note_from_other not in queryset


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
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == new_note.get_absolute_url()


class TestNoteReplyView:
    def test_get(self, person: Person, note: Note, rf: RequestFactory):
        request = rf.get(reverse("activitypub:note-reply", kwargs={"pk": note.pk}))
        request.user = person.user
        response = views.note_reply_view(request, pk=note.pk)
        assert response.status_code == HTTPStatus.OK

    def test_form_valid(self, person: Person, note: Note, rf: RequestFactory):
        content = "This is a reply."
        request = rf.post(
            reverse("activitypub:note-reply", kwargs={"pk": note.pk}),
            {"content": content},
        )
        request.user = person.user
        response = views.note_reply_view(request, pk=note.pk)

        reply_note = Note.objects.get(content=content)
        assert reply_note.author == person
        assert reply_note.in_reply_to == note
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reply_note.get_absolute_url()


class TestPersonDetailView:
    def test_get_context_data(self, person: Person):
        batch_size = 3
        NoteFactory.create_batch(batch_size, author=person)
        view = views.PersonDetailView()
        view.object = person

        context = view.get_context_data()

        assert "note_list" in context
        assert len(context["note_list"]) == batch_size
        assert list(context["note_list"]) == list(
            person.notes.order_by("-created").all()
        )


class TestPersonCreateView:
    def test_test_func(self, rf: RequestFactory, person: Person, settings, user: User):
        # Unauthenticated
        noauth_request = rf.get("/fake-url/")
        noauth_request.user = AnonymousUser()

        noauth_response = views.person_create_view(noauth_request)

        assert isinstance(noauth_response, HttpResponseRedirect)
        assert noauth_response.status_code == HTTPStatus.FOUND
        assert noauth_response.url == f"{reverse(settings.LOGIN_URL)}?next=/fake-url/"

        # Authenticated, with person
        auth_request_with_person = rf.get("/fake-url/")
        auth_request_with_person.user = person.user

        with pytest.raises(PermissionDenied):
            views.person_create_view(auth_request_with_person)

        # Authenticated, no person
        auth_request_no_person = rf.get("/fake-url/")
        auth_request_no_person.user = user
        response = views.person_create_view(auth_request_no_person)
        assert response.status_code == HTTPStatus.OK

    def test_create_person(self, user: User, rf: RequestFactory):
        assert not hasattr(user, "person")
        request = rf.post(reverse("activitypub:person-create"))
        request.user = user

        response = views.person_create_view(request)

        user.refresh_from_db()
        assert hasattr(user, "person")
        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == user.person.get_absolute_url()


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
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == person.get_absolute_url()
