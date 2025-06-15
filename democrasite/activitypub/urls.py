"""URLs for ActivityPub views."""

from django.urls import path

from . import views

app_name = "activitypub"
urlpatterns = [
    path("notes/", views.note_list_view, name="note-list"),
    path("notes/following/", views.user_following_notes_view, name="following-notes"),
    path("notes/my/", views.user_notes_view, name="my-notes"),
    path("notes/<int:pk>/", views.note_detail_view, name="note-detail"),
    path("notes/create/", views.note_create_view, name="note-create"),
    path("notes/<int:pk>/reply/", views.note_reply_view, name="note-reply"),
    path("person/create/", views.person_create_view, name="person-create"),
]
