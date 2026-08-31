from django.shortcuts import render
from rest_framework.views import APIView
from .models import *
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
# from .forms import RegisterForm
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from courses.models import Course
from lectures.models import Lecture
from timetable.models import Timetable

class LoginView(APIView):

    def get(self, request):
        return render(request, "accounts/login.html")

    def post(self, request):
        print('logging in..')
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, "accounts/login.html")

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is None:
            messages.error(request, "Invalid email or password.")
            return render(request, "accounts/login.html")

        login(request, user)
        print("LOGGED IN USER:", request.user)
        print("AUTHENTICATED:", request.user.is_authenticated)  

        return redirect("dashboard")

class RegisterView(APIView):

    def get(self, request):
        return render(request, "accounts/register.html")

    def post(self, request):
        print("REGISTER POST HIT")
        print(request.data)

        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        email = request.data.get("email")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")
        role = request.data.get("role")
        department = request.data.get("department")

        if password != confirm_password:
            return render(
                request,
                "accounts/register.html",
                {"error": "Passwords do not match"}
            )

        if not all([
            first_name,
            last_name,
            email,
            role,
            password,
            confirm_password
        ]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "accounts/register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, "accounts/register.html")

        if role not in ["student", "lecturer"]:
            messages.error(request, "Invalid account role.")
            return render(request, "accounts/register.html")

        User.objects.create_user(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            role=role,
            department=department
        )

        return redirect("login")

class LogoutView(APIView):

    def post(self, request):
        logout(request)

        return redirect("login")

@login_required(login_url="login")
def profile_view(request):

    user = request.user

    # ==========================================
    # UPDATE PROFILE
    # ==========================================

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        if not full_name:
            messages.error(
                request,
                "Your name cannot be empty."
            )

            return redirect("profile")


        name_parts = full_name.split(
            maxsplit=1
        )

        user.first_name = name_parts[0]

        if len(name_parts) > 1:
            user.last_name = name_parts[1]
        else:
            user.last_name = ""

        user.save(
            update_fields=[
                "first_name",
                "last_name"
            ]
        )

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("profile")


    # ==========================================
    # ACADEMIC INFORMATION
    # ==========================================

    department = getattr(
        user,
        "department",
        ""
    )


    if user.role == "lecturer":

        courses_taught = (
            Course.objects
            .filter(lecturer=user)
            .count()
        )

        lectures_created = (
            Lecture.objects
            .filter(lecturer=user)
            .count()
        )

        academic_stats = {
            "courses_taught": courses_taught,
            "lectures_created": lectures_created,
        }


    else:

        # We don't currently have a student enrollment model,
        # so courses on the student's timetable act as their
        # current academic courses.
        courses_enrolled = (
            Timetable.objects
            .filter(owner=user)
            .values("course_id")
            .distinct()
            .count()
        )

        # Students do not create recordings.
        # This represents lectures they can access.
        lectures_available = (
            Lecture.objects
            .filter(status="completed")
            .count()
        )

        academic_stats = {
            "courses_enrolled": courses_enrolled,
            "lectures_available": lectures_available,
        }


    context = {
        "department": department,
        **academic_stats,
    }


    return render(
        request,
        "accounts/profile.html",
        context
    )


@login_required(login_url="login")
def change_password(request):

    if request.method == "GET":

        return render(
            request,
            "accounts/change_password.html"
        )


    current_password = request.POST.get(
        "current_password"
    )

    new_password = request.POST.get(
        "new_password"
    )

    confirm_password = request.POST.get(
        "confirm_password"
    )


    if not request.user.check_password(
        current_password
    ):

        messages.error(
            request,
            "Your current password is incorrect."
        )

        return redirect(
            "change_password"
        )


    if new_password != confirm_password:

        messages.error(
            request,
            "The new passwords do not match."
        )

        return redirect(
            "change_password"
        )


    try:

        validate_password(
            new_password,
            request.user
        )

    except ValidationError as error:

        for message in error.messages:
            messages.error(
                request,
                message
            )

        return redirect(
            "change_password"
        )


    request.user.set_password(
        new_password
    )

    request.user.save()

    # Keeps the user logged in after changing password
    update_session_auth_hash(
        request,
        request.user
    )

    messages.success(
        request,
        "Password changed successfully."
    )

    return redirect(
        "profile"
    )


@login_required(login_url="login")
@require_POST
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been signed out."
    )

    return redirect(
        "login"
    )

from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from courses.models import Course
from lectures.models import Lecture
from timetable.models import Timetable


class DashboardView(LoginRequiredMixin, View):

    login_url = "login"

    def get(self, request):

        user = request.user

        now = timezone.localtime()
        today = timezone.localdate()
        day_name = today.strftime("%A")


        # ==============================
        # COURSES + LECTURES
        # ==============================

        if user.role == "lecturer":

            courses = Course.objects.filter(
                lecturer=user
            )

            lectures = Lecture.objects.filter(
                lecturer=user
            )

        else:

            courses = Course.objects.all()

            lectures = Lecture.objects.all()


        # ==============================
        # STATISTICS
        # ==============================

        total_courses = courses.count()

        total_lectures = lectures.count()

        # We don't currently store recording duration
        hours_recorded = "0h"


        # ==============================
        # TODAY'S SCHEDULE
        # ==============================

        todays_schedule = (
            Timetable.objects
            .filter(
                owner=user,
                day__iexact=day_name
            )
            .select_related("course")
            .order_by("start_time")
        )

        classes_today = todays_schedule.count()

        now = timezone.localtime()
        today = now.date()

        weekday_order = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }


        timetable_entries = (
            Timetable.objects
            .filter(owner=user)
            .select_related("course")
        )


        upcoming_classes = []


        for entry in timetable_entries:

            entry_day = entry.day.capitalize()

            if entry_day not in weekday_order:
                continue

            target_weekday = weekday_order[entry_day]

            days_ahead = (
                target_weekday - today.weekday()
            ) % 7

            class_date = (
                today + timedelta(days=days_ahead)
            )

            class_datetime = timezone.make_aware(
                datetime.combine(
                    class_date,
                    entry.start_time
                )
            )

            # If today's occurrence already happened,
            # use next week's occurrence.
            if class_datetime <= now:

                class_date += timedelta(days=7)

                class_datetime = timezone.make_aware(
                    datetime.combine(
                        class_date,
                        entry.start_time
                    )
                )


            upcoming_classes.append({
                "entry": entry,
                "datetime": class_datetime,
            })


        upcoming_classes.sort(
            key=lambda item: item["datetime"]
        )


        upcoming_classes = upcoming_classes[:5]


        # ==============================
        # RECENT LECTURES
        # ==============================

        recent_lectures = (
            lectures
            .select_related(
                "course",
                "lecturer"
            )
            .order_by("-created_at")[:5]
        )


        # ==============================
        # NEXT CLASS
        # ==============================

        day_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        timetable_entries = (
            Timetable.objects
            .filter(owner=user)
            .select_related("course")
        )

        next_class = None
        next_class_datetime = None


        for entry in timetable_entries:

            try:
                entry_day_index = day_order.index(
                    entry.day
                )

            except ValueError:
                continue


            today_index = today.weekday()

            days_ahead = (
                entry_day_index - today_index
            ) % 7


            class_date = (
                today
                + timedelta(days=days_ahead)
            )


            class_datetime = timezone.make_aware(
                datetime.combine(
                    class_date,
                    entry.start_time
                ),
                timezone.get_current_timezone()
            )


            # If today's class already started,
            # move this timetable entry to next week
            if class_datetime <= now:

                class_datetime += timedelta(
                    days=7
                )


            if (
                next_class_datetime is None
                or class_datetime < next_class_datetime
            ):

                next_class = entry
                next_class_datetime = class_datetime


        # ==============================
        # NEXT CLASS MESSAGE
        # ==============================

        next_class_message = None

        if (
            next_class
            and next_class_datetime
        ):

            difference = (
                next_class_datetime - now
            )

            total_minutes = int(
                difference.total_seconds()
                // 60
            )


            if total_minutes < 60:

                next_class_message = (
                    f"Starts in "
                    f"{total_minutes} minute"
                    f"{'' if total_minutes == 1 else 's'}."
                )


            elif total_minutes < 1440:

                hours = (
                    total_minutes // 60
                )

                minutes = (
                    total_minutes % 60
                )


                if minutes:

                    next_class_message = (
                        f"Starts in "
                        f"{hours}h "
                        f"{minutes}m."
                    )

                else:

                    next_class_message = (
                        f"Starts in "
                        f"{hours} hour"
                        f"{'' if hours == 1 else 's'}."
                    )


            else:

                days = (
                    total_minutes // 1440
                )

                next_class_message = (
                    f"Starts in "
                    f"{days} day"
                    f"{'' if days == 1 else 's'}."
                )


        context = {
            "total_lectures": total_lectures,
            "total_courses": total_courses,
            "hours_recorded": hours_recorded,
            "classes_today": classes_today,
            "todays_schedule": todays_schedule,
            "recent_lectures": recent_lectures,
            "upcoming_classes": upcoming_classes,
        }


        return render(
            request,
            "dashboard/dashboard.html",
            context
        )