from typing import TYPE_CHECKING

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

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


class NoteForm(forms.ModelForm):
    """Form for creating or replying to a note."""

    content = forms.CharField(
        max_length=500,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Share your thoughts..."}
        ),
        help_text="Your note content (max 500 characters).",
    )

    class Meta:
        model = Note
        fields = ["content"]


class NoteCreateView(UserProfileMixin, CreateView):
    model = Note
    form_class = NoteForm

    def form_valid(self, form):
        assert self.request.user.is_authenticated  # type guard
        form.instance.author = self.request.user.person
        return super().form_valid(form)


note_create_view = NoteCreateView.as_view()


class NoteReplyView(UserProfileMixin, CreateView):
    model = Note
    form_class = NoteForm

    def form_valid(self, form):
        assert self.request.user.is_authenticated  # type guard
        form.instance.author = self.request.user.person
        form.instance.in_reply_to_id = self.kwargs["pk"]
        return super().form_valid(form)


note_reply_view = NoteReplyView.as_view()


class PersonDetailView(UserProfileMixin, DetailView):
    model = Person

    slug_field = "user__username"
    slug_url_kwarg = "username"

    def get_object(self, queryset=None):
        """Get the Person object by username."""
        person = super().get_object(queryset)
        person.ordered_notes = person.notes.order_by("-created").all()
        return person


person_detail_view = PersonDetailView.as_view()


class PersonCreateView(UserPassesTestMixin, CreateView):
    model = Person
    fields = []

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

    def get_success_url(self):
        """Redirect to the note list after creating a Person profile."""
        messages.success(self.request, "Your ActivityPub profile has been created.")
        return reverse("activitypub:note-list")


person_create_view = PersonCreateView.as_view()


class PersonForm(forms.ModelForm):
    """Form for creating or updating a person's profile."""

    bio = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Describe yourself"}),
        help_text="Your bio content (max 500 characters).",
    )

    class Meta:
        model = Person
        fields = ["bio"]


class PersonUpdateView(UserProfileMixin, UpdateView):
    model = Person
    form_class = PersonForm

    def get_object(self, queryset=None):
        """Get the Person object for the current user."""
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.person


person_update_view = PersonUpdateView.as_view()
