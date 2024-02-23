from django.contrib import admin

# Register your models here.

from .models import Offer, CalendarEvent

admin.site.register(Offer)
admin.site.register(CalendarEvent)
