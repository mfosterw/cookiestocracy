from django import forms

from .models import Note
from .models import Person


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
