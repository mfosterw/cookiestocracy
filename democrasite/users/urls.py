"""URLs relating to users and accounts, if not defined in allauth."""

from django.urls import path

from democrasite.users import views

app_name = "users"
urlpatterns = [
    path("redirect/", view=views.user_redirect_view, name="redirect"),
    path("update/", view=views.user_update_view, name="update"),
    path("<str:username>/", view=views.user_detail_view, name="detail"),
]
