from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person

# Register your models here.
admin.site.register(Person, SimpleHistoryAdmin)
admin.site.register(Note, SimpleHistoryAdmin)
