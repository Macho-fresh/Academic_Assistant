from django.db import models
from django.conf import settings


class Notification(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    timetable = models.ForeignKey(
        "timetable.Timetable",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class_date = models.DateField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title