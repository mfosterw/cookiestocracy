"""This module registers Webiscite models for usage on the Django admin site"""
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from .models import Bill

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://django-allauth.readthedocs.io/en/stable/advanced.html#admin
    admin.site.login = login_required(admin.site.login)  # type: ignore[method-assign]

# Register your models here.
admin.site.register(Bill)
