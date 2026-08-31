from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from lectures.models import *
from django.db.models import Count, Q

from .models import Course


User = get_user_model()


class AddCourseView(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request):
        lecturers = User.objects.filter(
            role="lecturer"
        ).order_by("first_name", "last_name")

        context = {
            "lecturers": lecturers,
            "values": {},
            "errors": {},
        }

        return render(
            request,
            "courses/add_course.html",
            context
        )

    def post(self, request):
        course_code = request.POST.get(
            "course_code",
            ""
        ).strip()

        course_title = request.POST.get(
            "course_title",
            ""
        ).strip()

        lecturer_id = request.POST.get(
            "lecturer"
        )

        department = request.POST.get(
            "department",
            ""
        ).strip()

        academic_session = request.POST.get(
            "academic_session",
            ""
        ).strip()

        semester = request.POST.get(
            "semester",
            ""
        )

        values = {
            "course_code": course_code,
            "course_title": course_title,
            "lecturer": lecturer_id,
            "department": department,
            "academic_session": academic_session,
            "semester": semester,
        }

        errors = {}

        if not course_code:
            errors["course_code"] = (
                "Course code is required."
            )

        if not course_title:
            errors["course_title"] = (
                "Course title is required."
            )

        if not semester:
            errors["semester"] = (
                "Please select a semester."
            )

        if semester not in [
            "first",
            "second",
        ]:
            errors["semester"] = (
                "Invalid semester selected."
            )

        lecturer = None

        if request.user.role == "lecturer":
            lecturer = request.user

        else:
            if not lecturer_id:
                errors["lecturer"] = (
                    "Please select a lecturer."
                )

            else:
                try:
                    lecturer = User.objects.get(
                        id=lecturer_id,
                        role="lecturer"
                    )

                except User.DoesNotExist:
                    errors["lecturer"] = (
                        "The selected lecturer does not exist."
                    )

        if Course.objects.filter(
            course_code__iexact=course_code
        ).exists():
            errors["course_code"] = (
                "A course with this code already exists."
            )

        if academic_session:
            session_parts = academic_session.split("/")

            if (
                len(session_parts) != 2
                or not session_parts[0].isdigit()
                or not session_parts[1].isdigit()
            ):
                errors["academic_session"] = (
                    "Use a format like 2026/2027."
                )

        if errors:
            lecturers = User.objects.filter(
                role="lecturer"
            ).order_by(
                "first_name",
                "last_name"
            )

            context = {
                "lecturers": lecturers,
                "values": values,
                "errors": errors,
            }

            return render(
                request,
                "courses/add_course.html",
                context
            )

        Course.objects.create(
            course_code=course_code,
            course_title=course_title,
            lecturer=lecturer,
            department=department,
            academic_session=academic_session,
            semester=semester,
        )

        messages.success(
            request,
            "Course added successfully."
        )

        return redirect("courses")


@login_required(login_url="login")
def course_list(request):

    query = request.GET.get("q", "").strip()

    courses = (
        Course.objects
        .select_related("lecturer")
        .annotate(
            lecture_count=Count("lecture")
        )
        .order_by("course_code")
    )

    if query:
        courses = courses.filter(
            Q(course_code__icontains=query) |
            Q(course_title__icontains=query)
        )

    context = {
        "courses": courses,
    }

    return render(
        request,
        "courses/course_list.html",
        context
    )


@login_required(login_url="login")
def course_detail(request, course_id):

    course = get_object_or_404(
        Course.objects.select_related("lecturer"),
        id=course_id
    )

    lectures = (
        Lecture.objects
        .filter(course=course)
        .order_by("-created_at")
    )

    total_lectures = lectures.count()

    last_lecture = lectures.first()

    last_lecture_date = (
        last_lecture.created_at
        if last_lecture
        else None
    )

    context = {
        "course": course,
        "lectures": lectures,
        "total_lectures": total_lectures,
        "total_recorded": "0h 0m",
        "last_lecture_date": last_lecture_date,
        "processed_count": 0,
    }

    return render(
        request,
        "courses/course_detail.html",
        context
    )