from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from courses.models import Course
from .models import Timetable
from datetime import datetime


class TimetableView(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request):
        timetable_entries = Timetable.objects.filter(
            owner=request.user
        ).select_related("course")

        next_class = self.get_next_class(timetable_entries)

        context = {
            "timetable_entries": timetable_entries,
            "next_class": next_class,
        }

        return render(
            request,
            "timetable/timetable.html",
            context
        )

    def get_next_class(self, timetable_entries):
        now = datetime.now()

        day_numbers = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        next_entry = None
        shortest_difference = None
        next_datetime = None

        for entry in timetable_entries:

            class_day_number = day_numbers.get(entry.day.lower())

            if class_day_number is None:
                continue

            current_day_number = now.weekday()

            days_ahead = (
                class_day_number - current_day_number
            ) % 7

            class_datetime = datetime.combine(
                now.date() + timedelta(days=days_ahead),
                entry.start_time
            )

            # If the class is today but has already started,
            # move it to next week.
            if class_datetime <= now:
                class_datetime += timedelta(days=7)

            difference = class_datetime - now

            if (
                shortest_difference is None
                or difference < shortest_difference
            ):
                shortest_difference = difference
                next_entry = entry
                next_datetime = class_datetime

        if next_entry is None:
            return None

        return {
            "entry": next_entry,
            "datetime": next_datetime,
            "time_until": shortest_difference,
        }

class AddClassView(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request):
        courses = Course.objects.all()

        context = {
            "courses": courses,
        }

        return render(
            request,
            "timetable/add_class.html",
            context
        )

    def post(self, request):
        course_id = request.POST.get("course")
        day = request.POST.get("day")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        venue = request.POST.get("venue")
        reminder_time = request.POST.get("reminder_time")

        print("START TIME:", repr(start_time))
        print("END TIME:", repr(end_time))  
        if not course_id:
            messages.error(
                request,
                "Please select a course."
            )
            return redirect("add_class")

        if not day:
            messages.error(
                request,
                "Please select a day."
            )
            return redirect("add_class")

        if not start_time or not end_time:
            messages.error(
                request,
                "Start time and end time are required."
            )
            return redirect("add_class")

        try:
            start_time_obj = datetime.strptime(
                start_time,
                "%H:%M"
            ).time()

            end_time_obj = datetime.strptime(
                end_time,
                "%H:%M"
            ).time()

        except ValueError:
            messages.error(
                request,
                "Invalid time selected."
            )
            return redirect("add_class")

        if end_time_obj <= start_time_obj:
            messages.error(
                request,
                "End time must be later than start time."
            )
            return redirect("add_class")

        try:
            course = Course.objects.get(
                id=course_id
            )

        except Course.DoesNotExist:
            messages.error(
                request,
                "The selected course does not exist."
            )
            return redirect("add_class")

        conflicting_class = Timetable.objects.filter(
            owner=request.user,
            day=day,
            start_time__lt=end_time_obj,
            end_time__gt=start_time_obj,
        ).exists()

        if conflicting_class:
            messages.error(
                request,
                "This class conflicts with another timetable entry."
            )
            return redirect("add_class")

        Timetable.objects.create(
            owner=request.user,
            course=course,
            day=day,
            start_time=start_time_obj,
            end_time=end_time_obj,
            venue=venue,
            reminder_time=reminder_time or None,
        )

        messages.success(
            request,
            "Class added successfully."
        )

        return redirect("timetable")