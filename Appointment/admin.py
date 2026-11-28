from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("title", "service", "date", "time", "status", "user")
    list_filter = ("status", "service", "date")
    search_fields = ("user__username", "title", "description")
    date_hierarchy = "date"
    list_per_page = 25
