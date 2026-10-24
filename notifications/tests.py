
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Notification


User = get_user_model()


# =========================================================
# SHARED TEST SETUP
# =========================================================

class NotificationTestBase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="student1",
            password="TestPass123!",
            role="student",
        )

        self.other_user = User.objects.create_user(
            username="student2",
            password="TestPass123!",
            role="student",
        )

        self.notification = Notification.objects.create(
            user=self.user,
            title="Lecture Reminder",
            message="Your lecture starts in 30 minutes.",
        )

        self.other_notification = Notification.objects.create(
            user=self.other_user,
            title="Assignment Reminder",
            message="Submit your assignment today.",
        )


# =========================================================
# NOTIFICATION MODEL TESTS
# =========================================================

class NotificationModelTests(NotificationTestBase):

    def test_create_notification(self):
        self.assertEqual(
            self.notification.title,
            "Lecture Reminder",
        )
        self.assertEqual(
            self.notification.message,
            "Your lecture starts in 30 minutes.",
        )
        self.assertEqual(
            self.notification.user,
            self.user,
        )

    def test_notification_is_unread_by_default(self):
        notification = Notification.objects.create(
            user=self.user,
            title="New Notification",
            message="This is a test.",
        )

        self.assertFalse(notification.is_read)

    def test_notification_string_representation(self):
        self.assertEqual(
            str(self.notification),
            "Lecture Reminder",
        )

    def test_notification_has_created_at(self):
        self.assertIsNotNone(
            self.notification.created_at,
        )

    def test_notification_can_be_marked_as_read(self):
        self.notification.is_read = True
        self.notification.save(update_fields=["is_read"])

        self.notification.refresh_from_db()

        self.assertTrue(self.notification.is_read)

    def test_notification_can_have_class_date(self):
        notification = Notification.objects.create(
            user=self.user,
            title="Class Reminder",
            message="Your class is scheduled.",
            class_date=date(2026, 10, 25),
        )

        self.assertEqual(
            notification.class_date,
            date(2026, 10, 25),
        )

    def test_class_date_can_be_empty(self):
        notification = Notification.objects.create(
            user=self.user,
            title="General Notice",
            message="General information.",
        )

        self.assertIsNone(notification.class_date)

    def test_timetable_can_be_empty(self):
        self.assertIsNone(self.notification.timetable)

    def test_deleting_user_deletes_notifications(self):
        notification_id = self.notification.pk

        self.user.delete()

        self.assertFalse(
            Notification.objects.filter(
                pk=notification_id
            ).exists()
        )


# =========================================================
# UNREAD NOTIFICATIONS VIEW TESTS
# =========================================================

class UnreadNotificationsViewTests(NotificationTestBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("unread_notifications")

    def test_login_is_required(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_authenticated_user_receives_json(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/json",
        )

    def test_returns_only_current_users_unread_notifications(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.get(self.url)
        data = response.json()

        self.assertEqual(len(data["notifications"]), 1)
        self.assertEqual(
            data["notifications"][0]["id"],
            self.notification.id,
        )

    def test_does_not_return_other_users_notifications(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.get(self.url)
        notifications = response.json()["notifications"]

        notification_ids = [
            item["id"] for item in notifications
        ]

        self.assertNotIn(
            self.other_notification.id,
            notification_ids,
        )

    def test_read_notifications_are_excluded(self):
        self.notification.is_read = True
        self.notification.save(update_fields=["is_read"])

        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.json()["notifications"],
            [],
        )

    def test_returns_empty_list_when_no_unread_notifications(self):
        self.notification.is_read = True
        self.notification.save(update_fields=["is_read"])

        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.json(),
            {"notifications": []},
        )

    def test_response_contains_expected_fields(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.get(self.url)
        item = response.json()["notifications"][0]

        self.assertEqual(
            set(item.keys()),
            {"id", "title", "message"},
        )

    def test_notifications_are_ordered_oldest_first(self):
        older = self.notification

        newer = Notification.objects.create(
            user=self.user,
            title="Newer Notification",
            message="This notification is newer.",
        )

        # Set distinct timestamps so ordering is deterministic.
        from django.utils import timezone
        from datetime import timedelta

        Notification.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        Notification.objects.filter(pk=newer.pk).update(
            created_at=timezone.now()
        )

        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.get(self.url)
        items = response.json()["notifications"]

        self.assertEqual(
            [item["id"] for item in items],
            [older.id, newer.id],
        )

    def test_post_is_not_supported(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 405)


# =========================================================
# MARK NOTIFICATION READ VIEW TESTS
# =========================================================

class MarkNotificationReadViewTests(NotificationTestBase):

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "mark_notification_read",
            kwargs={
                "notification_id": self.notification.pk,
            },
        )

    def test_login_is_required(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_post_marks_notification_as_read(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"success": True},
        )

        self.notification.refresh_from_db()

        self.assertTrue(self.notification.is_read)

    def test_marking_already_read_notification_succeeds(self):
        self.notification.is_read = True
        self.notification.save(update_fields=["is_read"])

        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"success": True},
        )

    def test_other_users_notification_returns_404(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        url = reverse(
            "mark_notification_read",
            kwargs={
                "notification_id": self.other_notification.pk,
            },
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"error": "Notification not found."},
        )

        self.other_notification.refresh_from_db()

        self.assertFalse(self.other_notification.is_read)

    def test_nonexistent_notification_returns_404(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        url = reverse(
            "mark_notification_read",
            kwargs={"notification_id": 999999},
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"error": "Notification not found."},
        )

    def test_get_request_is_not_supported(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_marking_one_notification_does_not_change_another(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )

        self.client.post(self.url)

        self.other_notification.refresh_from_db()

        self.assertFalse(self.other_notification.is_read)
