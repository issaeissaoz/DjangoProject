from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("service", "date", "time", "status", "user")
    list_filter = ("status", "service", "date")
    search_fields = ("user__username", "service", "notes")
    date_hierarchy = "date"
    list_per_page = 25
