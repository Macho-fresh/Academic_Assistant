from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Timetable
from notifications.models import Notification


@shared_task
def check_upcoming_classes():

    now = timezone.localtime()

    today = now.date()

    day_name = now.strftime("%A")


    classes = (
        Timetable.objects
        .filter(
            day__iexact=day_name
        )
        .select_related(
            "course",
            "owner"
        )
    )


    for entry in classes:

        if entry.reminder_time is None:
            continue


        class_datetime = timezone.make_aware(
            datetime.combine(
                today,
                entry.start_time
            ),
            timezone.get_current_timezone()
        )


        reminder_datetime = (
            class_datetime
            - timedelta(
                minutes=entry.reminder_time
            )
        )


        # Task runs every minute, so check
        # whether the reminder falls in this minute.
        if (
            reminder_datetime
            <= now
            < reminder_datetime
            + timedelta(minutes=1)
        ):

            already_sent = (
                Notification.objects
                .filter(
                    user=entry.owner,
                    timetable=entry,
                    class_date=today
                )
                .exists()
            )


            if already_sent:
                continue


            message = (
                f"{entry.course.course_code} - "
                f"{entry.course.course_title} "
                f"starts at "
                f"{entry.start_time.strftime('%I:%M %p')}"
            )


            if entry.venue:

                message += (
                    f" at {entry.venue}"
                )


            message += "."


            Notification.objects.create(
                user=entry.owner,
                timetable=entry,
                class_date=today,
                title="Upcoming Class",
                message=message
            )