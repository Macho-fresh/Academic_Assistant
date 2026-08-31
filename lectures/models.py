from django.db import models
from courses.models import Course
from accounts.models import User

class Lecture(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    title = models.CharField(
        max_length=255
    )

    audio_file = models.FileField(
        upload_to="lectures/audio/", null=True
    )

    transcript = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.FloatField(
    default=0
    )
    
    def __str__(self):
        return f"{self.course.course_code} - {self.title}"


class TranscriptSegment(models.Model):
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name="transcript_segments"
    )

    start_seconds = models.FloatField()
    end_seconds = models.FloatField()
    text = models.TextField()

    @property
    def start_time(self):
        minutes = int(self.start_seconds // 60)
        seconds = int(self.start_seconds % 60)

        return f"{minutes:02d}:{seconds:02d}"


class TopicSegment(models.Model):

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name="topic_segments"
    )

    topic_label = models.CharField(
        max_length=255
    )

    start_seconds = models.FloatField()

    end_seconds = models.FloatField()

    @property
    def start_time(self):

        minutes = int(
            self.start_seconds // 60
        )

        seconds = int(
            self.start_seconds % 60
        )

        return f"{minutes:02d}:{seconds:02d}"


class LectureSummary(models.Model):
    lecture = models.OneToOneField(
        Lecture,
        on_delete=models.CASCADE,
        related_name="summary"
    )

    summary_text = models.TextField()
    key_points = models.JSONField(default=list)