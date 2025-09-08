"""This module registers Webiscite models for usage on the Django admin site"""

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Bill
from .models import PullRequest

# Register your models here.
admin.site.register(Bill, SimpleHistoryAdmin)
admin.site.register(PullRequest, SimpleHistoryAdmin)
