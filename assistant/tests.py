import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AssistantMessage

User = get_user_model()


class AssistantMessageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="InitialPass!927",
            role="student",
        )

    def test_create_message(self):
        message = AssistantMessage.objects.create(
            user=self.user,
            role="user",
            message="When is my next lecture?",
        )

        self.assertEqual(message.user, self.user)
        self.assertEqual(message.role, "user")
        self.assertEqual(message.message, "When is my next lecture?")
        self.assertEqual(message.metadata, {})
        self.assertIsNotNone(message.created_at)

    def test_string_representation(self):
        message = AssistantMessage.objects.create(
            user=self.user,
            role="assistant",
            message="Hello!",
        )

        self.assertEqual(str(message), f"{self.user} - assistant")

    def test_deleting_user_deletes_messages(self):
        AssistantMessage.objects.create(
            user=self.user,
            role="user",
            message="Hello",
        )

        self.user.delete()

        self.assertEqual(AssistantMessage.objects.count(), 0)


class AssistantViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="InitialPass!927",
            role="student",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="InitialPass!927",
            role="student",
        )
        self.url = reverse("assistant")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
        )

    def test_authenticated_user_sees_assistant_page(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "assistant/assistant.html")
        self.assertEqual(response.context["active_nav"], "assistant")

    def test_user_only_sees_their_own_messages(self):
        self.client.force_login(self.user)

        own_message = AssistantMessage.objects.create(
            user=self.user,
            role="user",
            message="My question",
        )

        AssistantMessage.objects.create(
            user=self.other_user,
            role="user",
            message="Another user's question",
        )

        response = self.client.get(self.url)

        self.assertEqual(
            list(response.context["assistant_messages"]),
            [own_message],
        )


class AskAssistantViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="InitialPass!927",
            role="student",
        )
        self.client.force_login(self.user)
        self.url = reverse("ask_assistant")

    def post_json(self, data):
        return self.client.post(
            self.url,
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            self.url,
            data="{invalid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"error": "Invalid request."},
        )
        self.assertEqual(AssistantMessage.objects.count(), 0)

    def test_missing_message_returns_400(self):
        response = self.post_json({})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"error": "Please enter a question."},
        )

    def test_empty_message_returns_400(self):
        response = self.post_json({"message": "   "})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"error": "Please enter a question."},
        )

    @patch("assistant.views.answer_question")
    def test_valid_question_saves_both_messages(self, mock_answer):
        result = {
            "answer": "Your next lecture is Software Engineering.",
            "lecture": "Software Engineering",
            "course": "COS 301",
            "lecture_id": 12,
            "timestamp": 125.5,
            "timestamp_display": "02:05",
            "match_type": "transcript",
        }
        mock_answer.return_value = result

        response = self.post_json({
            "message": "  When is my next lecture?  "
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), result)

        mock_answer.assert_called_once_with(
            self.user,
            "When is my next lecture?",
        )

        messages = list(
            AssistantMessage.objects.filter(
                user=self.user
            ).order_by("created_at", "pk")
        )

        self.assertEqual(len(messages), 2)

        user_message, assistant_message = messages

        self.assertEqual(user_message.role, "user")
        self.assertEqual(
            user_message.message,
            "When is my next lecture?",
        )

        self.assertEqual(assistant_message.role, "assistant")
        self.assertEqual(
            assistant_message.message,
            result["answer"],
        )

        self.assertEqual(
            assistant_message.metadata,
            {
                "lecture": "Software Engineering",
                "course": "COS 301",
                "lecture_id": 12,
                "timestamp": 125.5,
                "timestamp_display": "02:05",
                "match_type": "transcript",
            },
        )

    def test_anonymous_user_cannot_ask_question(self):
        self.client.logout()

        response = self.post_json({
            "message": "When is my next lecture?"
        })

        self.assertIn(response.status_code, (302, 401, 403))
        self.assertEqual(AssistantMessage.objects.count(), 0)


class ClearChatViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="InitialPass!927",
            role="student",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="InitialPass!927",
            role="student",
        )
        self.client.force_login(self.user)
        self.url = reverse("clear_chat")

    def test_clear_chat_deletes_own_messages(self):
        own_message = AssistantMessage.objects.create(
            user=self.user,
            role="user",
            message="My question",
        )

        other_message = AssistantMessage.objects.create(
            user=self.other_user,
            role="user",
            message="Another user's question",
        )

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "Chat cleared."},
        )

        self.assertFalse(
            AssistantMessage.objects.filter(
                pk=own_message.pk
            ).exists()
        )

        self.assertTrue(
            AssistantMessage.objects.filter(
                pk=other_message.pk
            ).exists()
        )

    def test_anonymous_user_cannot_clear_chat(self):
        self.client.logout()

        response = self.client.post(self.url)

        self.assertIn(response.status_code, (302, 401, 403))
