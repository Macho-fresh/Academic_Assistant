from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    ROLE_CHOICES = [
        ("student", "Student"),
        ("lecturer", "Lecturer"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    department = models.CharField(
        max_length=150,
        blank=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"