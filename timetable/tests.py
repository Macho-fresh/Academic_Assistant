
from datetime import datetime, timedelta, time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Course
from .models import Timetable
from .views import TimetableView


User = get_user_model()


class TimetableTestBase(TestCase):
    """Shared setup for timetable tests."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="student1",
            password="testpass123",
            role="student",
        )

        self.other_user = User.objects.create_user(
            username="student2",
            password="testpass123",
            role="student",
        )

        # Adjust these fields if your Course model differs.
        self.course = Course.objects.create(
            course_code="CSC401",
            course_title="Software Engineering",
            lecturer=self.user,
            semester="first semester",
            academic_session="2025/2026",
        )

        self.other_course = Course.objects.create(
            course_code="CSC402",
            course_title="Artificial Intelligence",
            lecturer=self.user,
            semester="first semester",
            academic_session="2025/2026",
        )

        self.timetable_url = reverse("timetable")
        self.add_class_url = reverse("add_class")

    def create_timetable_entry(
        self,
        owner=None,
        course=None,
        day="monday",
        start_time=time(9, 0),
        end_time=time(10, 0),
        venue="Room 101",
        reminder_time=15,
    ):
        return Timetable.objects.create(
            owner=owner or self.user,
            course=course or self.course,
            day=day,
            start_time=start_time,
            end_time=end_time,
            venue=venue,
            reminder_time=reminder_time,
        )


class TimetableModelTests(TimetableTestBase):
    def test_timetable_entry_is_created(self):
        entry = self.create_timetable_entry()

        self.assertEqual(Timetable.objects.count(), 1)
        self.assertEqual(entry.owner, self.user)
        self.assertEqual(entry.course, self.course)
        self.assertEqual(entry.day, "monday")
        self.assertEqual(entry.start_time, time(9, 0))
        self.assertEqual(entry.end_time, time(10, 0))

    def test_default_reminder_can_be_none(self):
        entry = self.create_timetable_entry(reminder_time=None)

        self.assertIsNone(entry.reminder_time)

    def test_venue_can_be_blank(self):
        entry = self.create_timetable_entry(venue="")

        self.assertEqual(entry.venue, "")

    def test_string_representation(self):
        entry = self.create_timetable_entry()

        self.assertEqual(
            str(entry),
            f"{self.course} - monday 09:00:00",
        )

    def test_deleting_owner_deletes_timetable_entries(self):
        entry = self.create_timetable_entry()
        entry_id = entry.id

        self.user.delete()

        self.assertFalse(
            Timetable.objects.filter(id=entry_id).exists()
        )

    def test_deleting_course_deletes_timetable_entries(self):
        entry = self.create_timetable_entry()
        entry_id = entry.id

        self.course.delete()

        self.assertFalse(
            Timetable.objects.filter(id=entry_id).exists()
        )


class TimetableViewTests(TimetableTestBase):
    def test_login_is_required(self):
        response = self.client.get(self.timetable_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_authenticated_user_can_view_timetable(self):
        self.client.login(
            username="student1",
            password="testpass123",
        )

        entry = self.create_timetable_entry()

        response = self.client.get(self.timetable_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "timetable/timetable.html")
        self.assertIn(entry, response.context["timetable_entries"])

    def test_user_only_sees_their_own_entries(self):
        self.client.login(
            username="student1",
            password="testpass123",
        )

        own_entry = self.create_timetable_entry()
        other_entry = self.create_timetable_entry(
            owner=self.other_user,
            course=self.other_course,
            day="tuesday",
        )

        response = self.client.get(self.timetable_url)
        entries = list(response.context["timetable_entries"])

        self.assertIn(own_entry, entries)
        self.assertNotIn(other_entry, entries)

    def test_empty_timetable_returns_no_next_class(self):
        self.client.login(
            username="student1",
            password="testpass123",
        )

        response = self.client.get(self.timetable_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["timetable_entries"].count(),
            0,
        )
        self.assertIsNone(response.context["next_class"])

    def test_timetable_entries_include_related_courses(self):
        self.client.login(
            username="student1",
            password="testpass123",
        )

        entry = self.create_timetable_entry()

        response = self.client.get(self.timetable_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["timetable_entries"].get(),
            entry,
        )


class NextClassTests(TimetableTestBase):
    def setUp(self):
        super().setUp()
        self.view = TimetableView()

    def test_returns_none_when_there_are_no_entries(self):
        result = self.view.get_next_class(
            Timetable.objects.none()
        )

        self.assertIsNone(result)

    def test_returns_the_soonest_upcoming_class(self):
        # Freeze time to Wednesday at 08:00.
        fixed_now = datetime(2026, 10, 21, 8, 0)

        today_entry = self.create_timetable_entry(
            day="wednesday",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        tomorrow_entry = self.create_timetable_entry(
            course=self.other_course,
            day="thursday",
            start_time=time(8, 30),
            end_time=time(9, 30),
        )

        with patch("timetable.views.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            mock_datetime.combine.side_effect = datetime.combine

            result = self.view.get_next_class(
                Timetable.objects.filter(owner=self.user)
            )

        self.assertEqual(result["entry"], today_entry)
        self.assertEqual(
            result["datetime"],
            datetime(2026, 10, 21, 9, 0),
        )
        self.assertEqual(
            result["time_until"],
            timedelta(hours=1),
        )

    def test_class_that_has_already_started_moves_to_next_week(self):
        # Wednesday, 21 October 2026, at 10:00.
        fixed_now = datetime(2026, 10, 21, 10, 0)

        entry = self.create_timetable_entry(
            day="wednesday",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        with patch("timetable.views.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            mock_datetime.combine.side_effect = datetime.combine

            result = self.view.get_next_class(
                Timetable.objects.filter(owner=self.user)
            )

        self.assertEqual(result["entry"], entry)
        self.assertEqual(
            result["datetime"],
            datetime(2026, 10, 28, 9, 0),
        )

    def test_invalid_day_is_ignored(self):
        # An invalid value can exist in the database even though
        # the model declares choices for the day field.
        entry = self.create_timetable_entry(day="invalid")

        result = self.view.get_next_class(
            Timetable.objects.filter(id=entry.id)
        )

        self.assertIsNone(result)


class AddClassViewTests(TimetableTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(
            username="student1",
            password="testpass123",
        )

    def valid_form_data(self, **overrides):
        data = {
            "course": str(self.course.id),
            "day": "monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "venue": "Room 101",
            "reminder_time": "15",
        }
        data.update(overrides)
        return data

    def test_login_is_required_to_open_add_class_page(self):
        self.client.logout()

        response = self.client.get(self.add_class_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_authenticated_user_can_open_add_class_page(self):
        response = self.client.get(self.add_class_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "timetable/add_class.html")
        self.assertIn(self.course, response.context["courses"])

    def test_class_is_added_successfully(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(),
        )

        self.assertRedirects(response, self.timetable_url)

        entry = Timetable.objects.get(owner=self.user)

        self.assertEqual(entry.course, self.course)
        self.assertEqual(entry.day, "monday")
        self.assertEqual(entry.start_time, time(9, 0))
        self.assertEqual(entry.end_time, time(10, 0))
        self.assertEqual(entry.venue, "Room 101")
        self.assertEqual(entry.reminder_time, 15)

    
    def test_missing_course_is_rejected(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(course=""),
            follow=True,
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 0)

        messages = list(response.context["messages"])
        self.assertTrue(
            any(
                "Please select a course." in str(message)
                for message in messages
            )
        )


    def test_missing_day_is_rejected(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(day=""),
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 0)

    def test_missing_start_time_is_rejected(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(start_time=""),
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 0)

    def test_missing_end_time_is_rejected(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(end_time=""),
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 0)

    def test_invalid_time_format_is_rejected(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(start_time="not-a-time"),
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 0)

    def test_end_time_must_be_later_than_start_time(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(
                start_time="10:00",
                end_time="09:00",
            ),
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 0)

    def test_end_time_cannot_equal_start_time(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(
                start_time="09:00",
                end_time="09:00",
            ),
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 0)

    def test_nonexistent_course_is_rejected(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(course="999999"),
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 0)

    def test_overlapping_class_is_rejected(self):
        self.create_timetable_entry(
            day="monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(
                start_time="09:30",
                end_time="10:30",
            ),
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 1)

    def test_class_inside_an_existing_class_is_rejected(self):
        self.create_timetable_entry(
            day="monday",
            start_time=time(9, 0),
            end_time=time(11, 0),
        )

        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(
                start_time="09:30",
                end_time="10:00",
            ),
        )

        self.assertRedirects(response, self.add_class_url)
        self.assertEqual(Timetable.objects.count(), 1)

    def test_overlapping_class_on_another_day_is_allowed(self):
        self.create_timetable_entry(
            day="monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(
                day="tuesday",
                start_time="09:30",
                end_time="10:30",
            ),
        )

        self.assertRedirects(response, self.timetable_url)
        self.assertEqual(Timetable.objects.count(), 2)

    def test_overlapping_class_for_another_user_is_allowed(self):
        self.create_timetable_entry(
            owner=self.other_user,
            day="monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(
                start_time="09:30",
                end_time="10:30",
            ),
        )

        self.assertRedirects(response, self.timetable_url)
        self.assertEqual(Timetable.objects.count(), 2)

    def test_back_to_back_classes_are_allowed(self):
        self.create_timetable_entry(
            day="monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(
                start_time="10:00",
                end_time="11:00",
            ),
        )

        self.assertRedirects(response, self.timetable_url)
        self.assertEqual(Timetable.objects.count(), 2)

    def test_blank_reminder_is_saved_as_none(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(reminder_time=""),
        )

        self.assertRedirects(response, self.timetable_url)

        entry = Timetable.objects.get(owner=self.user)
        self.assertIsNone(entry.reminder_time)

    def test_venue_can_be_blank_when_adding_class(self):
        response = self.client.post(
            self.add_class_url,
            self.valid_form_data(venue=""),
        )

        self.assertRedirects(response, self.timetable_url)

        entry = Timetable.objects.get(owner=self.user)
        self.assertEqual(entry.venue, "")

    def test_get_request_does_not_create_a_class(self):
        response = self.client.get(self.add_class_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Timetable.objects.count(), 0)
