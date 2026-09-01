from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from courses.models import Course
from lectures.models import Lecture
from timetable.models import Timetable


User = get_user_model()


class AcademicAssistantAPITestCase(APITestCase):

    def setUp(self):

        self.lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer@example.com",
            password="password123",
            first_name="Grace",
            last_name="Nnabugwu",
            role="lecturer"
        )

        self.student = User.objects.create_user(
            username="student1",
            email="student@example.com",
            password="password123",
            first_name="Michael",
            last_name="Student",
            role="student"
        )

        self.course = Course.objects.create(
            course_code="COS431",
            course_title="Compiler Construction",
            lecturer=self.lecturer,
            department="Computer Science",
            semester="First",
            academic_session="2026/2027"
        )

        self.lecture = Lecture.objects.create(
            course=self.course,
            lecturer=self.lecturer,
            title="Lexical Analysis",
            status="completed",
            transcript="Lexical analysis converts source code into tokens.",
            duration_seconds=120
        )


    # ==========================================
    # AUTHENTICATION
    # ==========================================

    def test_unauthenticated_user_cannot_access_lectures(self):

        response = self.client.get(
            reverse("lectures")
        )

        self.assertEqual(
            response.status_code,
            302
        )


    def test_authenticated_student_can_access_lectures(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("lectures")
        )

        self.assertEqual(
            response.status_code,
            200
        )


    def test_authenticated_lecturer_can_access_lectures(self):

        self.client.force_login(
            user=self.lecturer
        )

        response = self.client.get(
            reverse("lectures")
        )

        self.assertEqual(
            response.status_code,
            200
        )


    # ==========================================
    # LECTURE LIST
    # ==========================================

    def test_lecture_list_contains_existing_lecture(self):

        self.client.force_login(
            user=self.lecturer
        )

        response = self.client.get(
            reverse("lectures")
        )

        self.assertContains(
            response,
            "Lexical Analysis"
        )


    def test_lecturer_only_sees_their_own_lectures(self):

        second_lecturer = User.objects.create_user(
            username="lecturer2",
            email="lecturer2@example.com",
            password="password123",
            role="lecturer"
        )

        second_course = Course.objects.create(
            course_code="COS451",
            course_title="Artificial Intelligence",
            lecturer=second_lecturer,
            department="Computer Science",
            semester="First",
            academic_session="2026/2027"
        )

        Lecture.objects.create(
            course=second_course,
            lecturer=second_lecturer,
            title="Neural Networks",
            status="completed"
        )

        self.client.force_login(
            user=self.lecturer
        )

        response = self.client.get(
            reverse("lectures")
        )

        self.assertContains(
            response,
            "Lexical Analysis"
        )

        self.assertNotContains(
            response,
            "Neural Networks"
        )


    # ==========================================
    # LECTURE DETAIL
    # ==========================================

    def test_lecture_detail_page(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse(
                "lecture_detail",
                args=[self.lecture.id]
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "Lexical Analysis"
        )

        self.assertContains(
            response,
            "Lexical analysis converts source code into tokens."
        )


    def test_invalid_lecture_returns_404(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse(
                "lecture_detail",
                args=[9999]
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )


    # ==========================================
    # RECORD LECTURE PERMISSIONS
    # ==========================================

    def test_student_cannot_access_record_lecture(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("record_lecture")
        )

        self.assertEqual(
            response.status_code,
            302
        )


    def test_lecturer_can_access_record_lecture(self):

        self.client.force_login(
            user=self.lecturer
        )

        response = self.client.get(
            reverse("record_lecture")
        )

        self.assertEqual(
            response.status_code,
            200
        )


    # ==========================================
    # UPLOAD LECTURE PERMISSIONS
    # ==========================================

    def test_student_cannot_access_upload_lecture(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("upload_lecture")
        )

        self.assertEqual(
            response.status_code,
            302
        )


    def test_lecturer_can_access_upload_lecture(self):

        self.client.force_login(
            user=self.lecturer
        )

        response = self.client.get(
            reverse("upload_lecture")
        )

        self.assertEqual(
            response.status_code,
            200
        )


    # ==========================================
    # SEARCH
    # ==========================================

    def test_search_lectures_by_title(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("lectures"),
            {
                "q": "Lexical"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "Lexical Analysis"
        )


    def test_search_with_unknown_term_returns_no_lecture(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("lectures"),
            {
                "q": "Quantum Computing"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertNotContains(
            response,
            "Lexical Analysis"
        )


    # ==========================================
    # COURSE FILTER
    # ==========================================

    def test_filter_lectures_by_course(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("lectures"),
            {
                "course": self.course.id
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "Lexical Analysis"
        )


    # ==========================================
    # STATUS FILTER
    # ==========================================

    def test_filter_completed_lectures(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("lectures"),
            {
                "status": "completed"
            }
        )

        self.assertContains(
            response,
            "Lexical Analysis"
        )


    def test_failed_filter_does_not_show_completed_lecture(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("lectures"),
            {
                "status": "failed"
            }
        )

        self.assertNotContains(
            response,
            "Lexical Analysis"
        )


    # ==========================================
    # DELETE LECTURE
    # ==========================================

    def test_lecturer_can_delete_own_lecture(self):

        self.client.force_login(
            user=self.lecturer
        )

        response = self.client.post(
            reverse(
                "delete_lecture",
                args=[self.lecture.id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            Lecture.objects.filter(
                id=self.lecture.id
            ).exists()
        )


    def test_student_cannot_delete_lecture(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.post(
            reverse(
                "delete_lecture",
                args=[self.lecture.id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            Lecture.objects.filter(
                id=self.lecture.id
            ).exists()
        )


    def test_lecturer_cannot_delete_another_lecturers_lecture(self):

        other_lecturer = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="password123",
            role="lecturer"
        )

        self.client.force_login(
            user=other_lecturer
        )

        response = self.client.post(
            reverse(
                "delete_lecture",
                args=[self.lecture.id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            Lecture.objects.filter(
                id=self.lecture.id
            ).exists()
        )


    # ==========================================
    # TIMETABLE
    # ==========================================

    def test_user_can_view_their_timetable(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("timetable")
        )

        self.assertEqual(
            response.status_code,
            200
        )


    def test_timetable_only_shows_current_users_entries(self):

        Timetable.objects.create(
            owner=self.student,
            course=self.course,
            day="Monday",
            start_time="09:00",
            end_time="11:00",
            venue="Room 204"
        )

        Timetable.objects.create(
            owner=self.lecturer,
            course=self.course,
            day="Tuesday",
            start_time="12:00",
            end_time="14:00",
            venue="ICT Building"
        )

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("timetable")
        )

        self.assertContains(
            response,
            "Room 204"
        )

        self.assertNotContains(
            response,
            "ICT Building"
        )


    # ==========================================
    # DASHBOARD
    # ==========================================

    def test_dashboard_requires_authentication(self):

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(
            response.status_code,
            302
        )


    def test_dashboard_for_logged_in_user(self):

        self.client.force_login(
            user=self.student
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(
            response.status_code,
            200
        )


    def test_dashboard_contains_lecture_count(self):

        self.client.force_login(
            self.lecturer
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.context["total_lectures"],
            1
        )

    def test_dashboard_calculates_recorded_duration(self):

        self.client.force_login(
            self.lecturer
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.context["hours_recorded"],
            "2m"
        )