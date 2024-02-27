"""This module registers Webiscite models for usage on the Django admin site"""

from django.contrib import admin

from .models import Bill, PullRequest

# Register your models here.
admin.site.register(Bill)
admin.site.register(PullRequest)
