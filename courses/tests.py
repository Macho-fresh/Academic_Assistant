
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Course

User = get_user_model()


class CourseModelTests(TestCase):
    def setUp(self):
        self.lecturer = User.objects.create_user(
            username="lecturer@example.com",
            email="lecturer@example.com",
            password="SecurePass!927",
            first_name="Ada",
            last_name="Okafor",
            role="lecturer",
        )

    def test_create_course(self):
        course = Course.objects.create(
            course_code="COS301",
            course_title="Software Engineering",
            lecturer=self.lecturer,
            department="Computer Science",
            academic_session="2026/2027",
            semester="first semester",
        )

        self.assertEqual(course.course_code, "COS301")
        self.assertEqual(course.course_title, "Software Engineering")
        self.assertEqual(course.lecturer, self.lecturer)
        self.assertEqual(course.department, "Computer Science")
        self.assertEqual(course.academic_session, "2026/2027")
        self.assertEqual(course.semester, "first semester")

    def test_course_can_exist_without_lecturer(self):
        course = Course.objects.create(
            course_code="COS302",
            course_title="Algorithms",
            lecturer=self.lecturer,
        )

        self.lecturer.delete()
        course.refresh_from_db()

        self.assertIsNone(course.lecturer)

    def test_default_semester_is_first_semester(self):
        course = Course.objects.create(
            course_code="COS303",
            course_title="Database Systems",
        )

        self.assertEqual(course.semester, "first semester")

    def test_semester_choices(self):
        choices = dict(Course.SEMESTER_CHOICES)

        self.assertIn("first semester", choices)
        self.assertIn("second semseter", choices)


class AddCourseViewTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="SecurePass!927",
            role="student",
        )

        self.lecturer = User.objects.create_user(
            username="lecturer@example.com",
            email="lecturer@example.com",
            password="SecurePass!927",
            first_name="Ada",
            last_name="Okafor",
            role="lecturer",
        )

        self.url = reverse("add_course")

        self.valid_data = {
            "course_code": "COS301",
            "course_title": "Software Engineering",
            "lecturer": str(self.lecturer.pk),
            "department": "Computer Science",
            "academic_session": "2026/2027",
            # These are the values currently accepted by the view.
            "semester": "first",
        }

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
        )

    def test_get_displays_add_course_page(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courses/add_course.html")
        self.assertIn(self.lecturer, response.context["lecturers"])
        self.assertEqual(response.context["values"], {})
        self.assertEqual(response.context["errors"], {})

    def test_missing_course_code_is_rejected(self):
        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["course_code"] = ""

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("course_code", response.context["errors"])
        self.assertEqual(Course.objects.count(), 0)

    def test_missing_course_title_is_rejected(self):
        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["course_title"] = ""

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("course_title", response.context["errors"])
        self.assertEqual(Course.objects.count(), 0)

    def test_missing_semester_is_rejected(self):
        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["semester"] = ""

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("semester", response.context["errors"])
        self.assertEqual(Course.objects.count(), 0)

    def test_invalid_semester_is_rejected(self):
        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["semester"] = "summer"

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("semester", response.context["errors"])
        self.assertEqual(Course.objects.count(), 0)

    def test_missing_lecturer_is_rejected(self):
        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["lecturer"] = ""

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("lecturer", response.context["errors"])
        self.assertEqual(Course.objects.count(), 0)

    def test_student_cannot_be_selected_as_lecturer(self):
        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["lecturer"] = str(self.admin_user.pk)

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("lecturer", response.context["errors"])
        self.assertEqual(Course.objects.count(), 0)

    def test_duplicate_course_code_is_rejected_case_insensitively(self):
        Course.objects.create(
            course_code="COS301",
            course_title="Existing Course",
        )

        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["course_code"] = "cos301"

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("course_code", response.context["errors"])
        self.assertEqual(Course.objects.count(), 1)

    def test_invalid_academic_session_is_rejected(self):
        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["academic_session"] = "2026-2027"

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("academic_session", response.context["errors"])
        self.assertEqual(Course.objects.count(), 0)

    def test_valid_academic_session_format_is_accepted_by_validation(self):
        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["academic_session"] = "2026/2027"

        response = self.client.post(self.url, data)

        # The current view accepts "first" for semester validation.
        self.assertRedirects(response, reverse("courses"))
        course = Course.objects.get(course_code="COS301")
        self.assertEqual(course.academic_session, "2026/2027")

    def test_course_fields_are_trimmed(self):
        self.client.force_login(self.admin_user)
        data = self.valid_data.copy()
        data["course_code"] = "  COS301  "
        data["course_title"] = "  Software Engineering  "
        data["department"] = "  Computer Science  "

        self.client.post(self.url, data)

        course = Course.objects.get(course_code="COS301")
        self.assertEqual(course.course_title, "Software Engineering")
        self.assertEqual(course.department, "Computer Science")

    def test_lecturer_can_add_course_for_themselves(self):
        self.client.force_login(self.lecturer)
        data = self.valid_data.copy()
        data["lecturer"] = ""

        response = self.client.post(self.url, data)

        self.assertRedirects(response, reverse("courses"))
        course = Course.objects.get(course_code="COS301")
        self.assertEqual(course.lecturer, self.lecturer)


class CourseListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="SecurePass!927",
            role="student",
        )
        self.lecturer = User.objects.create_user(
            username="lecturer@example.com",
            email="lecturer@example.com",
            password="SecurePass!927",
            role="lecturer",
        )

        self.course1 = Course.objects.create(
            course_code="COS301",
            course_title="Software Engineering",
            lecturer=self.lecturer,
        )
        self.course2 = Course.objects.create(
            course_code="COS302",
            course_title="Database Systems",
            lecturer=self.lecturer,
        )

        self.url = reverse("courses")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
        )

    def test_authenticated_user_can_view_courses(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courses/course_list.html")
        self.assertEqual(
            list(response.context["courses"]),
            [self.course1, self.course2],
        )

    def test_search_matches_course_code(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url, {"q": "COS301"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["courses"]),
            [self.course1],
        )

    def test_search_matches_course_title_case_insensitively(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url, {"q": "DATABASE"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["courses"]),
            [self.course2],
        )

    def test_search_with_no_match_returns_empty_queryset(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url, {"q": "NONEXISTENT"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 0)


class CourseDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="SecurePass!927",
            role="student",
        )

        self.course = Course.objects.create(
            course_code="COS301",
            course_title="Software Engineering",
        )

        self.url = reverse("course_detail", args=[self.course.pk])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
        )

    def test_course_detail_page_loads(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courses/course_detail.html")
        self.assertEqual(response.context["course"], self.course)
        self.assertEqual(response.context["total_lectures"], 0)
        self.assertEqual(response.context["total_recorded"], "0s")
        self.assertIsNone(response.context["last_lecture_date"])
        self.assertEqual(response.context["processed_count"], 0)

    def test_nonexistent_course_returns_404(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("course_detail", args=[999999])
        )

        self.assertEqual(response.status_code, 404)
