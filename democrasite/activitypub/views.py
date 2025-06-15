from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView

from .models import Note
from .models import Person

if TYPE_CHECKING:
    from django.forms import ModelForm


class NoteListView(ListView):
    model = Note

    queryset = Note.objects.all().order_by("-created")


note_list_view = NoteListView.as_view()


class UserProfileMixin(UserPassesTestMixin):
    """Mixin to ensure the user has a Person profile."""

    request: HttpRequest

    def test_func(self):
        """Ensure the user has a Person profile."""
        if not self.request.user.is_authenticated:
            return False
        try:
            return bool(self.request.user.person)
        except Person.DoesNotExist:
            return False

    def handle_no_permission(self):
        """Redirect to note list if the user does not have a Person profile."""
        messages.error(
            self.request, "You must have an ActivityPub profile to access this page."
        )
        return HttpResponseRedirect(reverse("activitypub:note-list"))


class UserFollowingNotesView(UserProfileMixin, ListView):
    model = Note

    def get_queryset(self):
        assert self.request.user.is_authenticated  # type guard
        return Note.objects.filter(
            author__in=self.request.user.person.following.all()
        ).order_by("-created")


user_following_notes_view = UserFollowingNotesView.as_view()


class UserNotesView(UserProfileMixin, ListView):
    model = Note

    def get_queryset(self):
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.person.notes.order_by("-created")


user_notes_view = UserNotesView.as_view()


class NoteDetailView(DetailView):
    model = Note


note_detail_view = NoteDetailView.as_view()


class NoteCreateView(UserProfileMixin, CreateView):
    model = Note
    fields = ["content"]

    def form_valid(self, form):
        assert self.request.user.is_authenticated  # type guard
        form.instance.author = self.request.user.person
        return super().form_valid(form)


note_create_view = NoteCreateView.as_view()


class NoteReplyView(UserProfileMixin, CreateView):
    model = Note
    fields = ["content"]

    def get_initial(self):
        initial = super().get_initial()
        initial["in_reply_to"] = self.kwargs["pk"]
        return initial

    def form_valid(self, form):
        assert self.request.user.is_authenticated  # type guard
        form.instance.author = self.request.user.person
        form.instance.in_reply_to_id = self.kwargs["pk"]
        return super().form_valid(form)


note_reply_view = NoteReplyView.as_view()


class PersonCreateView(UserPassesTestMixin, CreateView):
    model = Person
    fields = []
    success_url = reverse_lazy("activitypub:note-list")

    def form_valid(self, form: "ModelForm[Person]"):
        assert self.request.user.is_authenticated  # type guard
        form.instance.user = self.request.user
        form.instance.private_key = "private_key_placeholder"
        form.instance.public_key = "public_key_placeholder"
        return super().form_valid(form)

    def test_func(self):
        """Ensure the user does not already have a Person profile."""
        if not self.request.user.is_authenticated:
            return False
        try:
            if self.request.user.person:
                return False
        except Person.DoesNotExist:
            return True


person_create_view = PersonCreateView.as_view()
