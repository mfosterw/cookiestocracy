from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from democrasite.social.models import Note
from democrasite.social.models import Person


@admin.register(Note)
class HistoryMpttAdmin(SimpleHistoryAdmin, MPTTModelAdmin):
    pass


admin.site.register(Person, SimpleHistoryAdmin)
