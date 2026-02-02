from functools import wraps
from http import HTTPStatus
from typing import TYPE_CHECKING

from django import forms
from django import http
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from .models import Note
from .models import Person

if TYPE_CHECKING:
    from django.forms import ModelForm  # pragma: no cover


class NoteListView(ListView):
    model = Note


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


def require_user_profile(view_func):
    """Decorator to ensure the user has a Person profile."""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return http.HttpResponse("Login required", status=HTTPStatus.UNAUTHORIZED)
        if not hasattr(request.user, "person"):
            return http.HttpResponse("Profile required", status=HTTPStatus.FORBIDDEN)
        return view_func(request, *args, **kwargs)

    return _wrapped_view


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


@require_POST
@require_user_profile
def note_like_view(request: HttpRequest, pk: int) -> http.HttpResponse:
    assert request.user.is_authenticated  # type guard

    note = get_object_or_404(Note, pk=pk)
    note.like(request.user.person)

    return http.JsonResponse({"likes": note.likes.count()})


@require_POST
@require_user_profile
def note_repost_view(request: HttpRequest, pk: int) -> http.HttpResponse:
    assert request.user.is_authenticated  # type guard

    note = get_object_or_404(Note, pk=pk)
    note.repost(request.user.person)

    return http.JsonResponse({"reposts": note.reposts.count()})


class PersonDetailView(DetailView):
    model = Person

    slug_field = "user__username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["note_list"] = Note.objects.get_person_notes(self.object)
        if hasattr(self.request.user, "person"):
            context["user_following_person"] = self.request.user.person.is_following(
                self.object
            )
        return context


person_detail_view = PersonDetailView.as_view()


class PersonCreateView(SuccessMessageMixin, CreateView):
    model = Person
    fields = []

    success_message = "Profile created successfully."

    http_method_names = ["post"]

    def post(self, request):
        """Ensure the user does not already have a Person profile."""
        if not self.request.user.is_authenticated:
            messages.info(request, "You must be logged in to do that.")
            return redirect_to_login(reverse("activitypub:note-list"))
        try:
            if self.request.user.person:
                messages.info(request, "You already have an ActivityPub Profile!")
                return redirect(
                    "activitypub:person-detail",
                    username=request.user.person.display_name,
                )
        except Person.DoesNotExist:
            pass
        return super().post(request)

    def form_valid(self, form: "ModelForm[Person]"):
        assert self.request.user.is_authenticated  # type guard
        form.instance.user = self.request.user
        form.instance.private_key = "private_key_placeholder"
        form.instance.public_key = "public_key_placeholder"
        return super().form_valid(form)


person_create_view = PersonCreateView.as_view()


class PersonForm(forms.ModelForm):
    """Form for creating or updating a person's profile."""

    bio = forms.CharField(
        max_length=500,
        required=False,
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


class PersonFollowingNotesView(UserProfileMixin, ListView):
    model = Note

    def get_queryset(self):
        assert self.request.user.is_authenticated  # type guard
        return Note.objects.get_person_following_notes(self.request.user.person)


person_following_notes_view = PersonFollowingNotesView.as_view()


@require_POST
@require_user_profile
def person_follow_view(request: HttpRequest, username: str) -> http.HttpResponse:
    """Follow a user by username."""
    assert request.user.is_authenticated  # type guard

    person = get_object_or_404(Person, user__username=username)
    request.user.person.follow(person)

    return JsonResponse({"followers": person.followers.count()})
