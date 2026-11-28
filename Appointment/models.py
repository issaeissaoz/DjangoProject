from django.conf import settings
from django.db import models


class Appointment(models.Model):
    class Service(models.TextChoices):
        GENERAL = "general", "General consultation"
        DENTAL = "dental", "Dental check-up"
        EYE = "eye", "Eye examination"
        PHYSIO = "physio", "Physiotherapy"
        COUNSELLING = "counselling", "Counselling"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=120)
    service = models.CharField(max_length=32, choices=Service.choices)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]

    def __str__(self):
        return f"{self.title} on {self.date:%d %b %Y} at {self.time:%H:%M}"
