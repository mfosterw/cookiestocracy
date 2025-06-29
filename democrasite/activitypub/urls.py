"""URLs for ActivityPub views."""

from django.urls import path

from . import views

app_name = "activitypub"
urlpatterns = [
    path("notes/", views.note_list_view, name="note-list"),
    path("notes/create/", views.note_create_view, name="note-create"),
    path("notes/<int:pk>/", views.note_detail_view, name="note-detail"),
    path("notes/<int:pk>/reply/", views.note_reply_view, name="note-reply"),
    path("notes/<int:pk>/like/", views.note_like_view, name="note-like"),
    path("notes/<int:pk>/repost/", views.note_repost_view, name="note-repost"),
    # Person-related views
    path("person/create/", views.person_create_view, name="person-create"),
    path("person/update/", views.person_update_view, name="person-update"),
    path(
        "person/following/", views.person_following_notes_view, name="following-notes"
    ),
    path("person/<str:username>/", views.person_detail_view, name="person-detail"),
    path(
        "person/<str:username>/follow/", views.person_follow_view, name="person-follow"
    ),
]
