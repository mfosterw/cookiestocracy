from django.contrib import admin

from democrasite.activitypub.models import Note
from democrasite.activitypub.models import Person

# Register your models here.
admin.site.register(Person)
admin.site.register(Note)
