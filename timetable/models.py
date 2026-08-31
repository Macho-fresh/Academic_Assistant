from django.db import models
from accounts.models import User
from courses.models import Course

from django.conf import settings
from django.db import models


class Timetable(models.Model):
    DAY_CHOICES = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
        ("saturday", "Saturday"),
    ]

    REMINDER_CHOICES = [
        (10, "10 minutes before"),
        (15, "15 minutes before"),
        (30, "30 minutes before"),
        (60, "1 hour before"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="timetable_entries"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="timetable_entries"
    )

    day = models.CharField(
        max_length=20,
        choices=DAY_CHOICES
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    venue = models.CharField(
        max_length=150,
        blank=True
    )

    reminder_time = models.PositiveIntegerField(
        choices=REMINDER_CHOICES,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.course} - {self.day} {self.start_time}"