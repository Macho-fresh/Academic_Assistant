from django.db import models
from accounts.models import User

class Course(models.Model):
    course_code = models.CharField(
        max_length=20
    )

    course_title = models.CharField(
        max_length=200
    )

    lecturer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    department = models.CharField(
        max_length=150,
        blank=True
    )

    academic_session = models.CharField(
        max_length=20,
        blank=True
    )

    SEMESTER_CHOICES = [
        ("first semester", "First Semester"),
        ("second semseter", "Second Semester"),
    ]

    semester = models.CharField(choices=SEMESTER_CHOICES, max_length=20, default="first semester")