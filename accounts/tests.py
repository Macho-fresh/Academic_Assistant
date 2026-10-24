from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="InitialPass!927",
            first_name="Ada",
            last_name="Okafor",
            role="student",
            department="Computer Science",
        )

    def test_user_is_created_with_expected_fields(self):
        self.assertEqual(self.user.email, "student@example.com")
        self.assertEqual(self.user.role, "student")
        self.assertEqual(self.user.department, "Computer Science")
        self.assertTrue(self.user.check_password("InitialPass!927"))

    def test_string_representation_is_full_name(self):
        self.assertEqual(str(self.user), "Ada Okafor")

    def test_user_role_choices_include_student_and_lecturer(self):
        role_choices = dict(User.ROLE_CHOICES)
        self.assertIn("student", role_choices)
        self.assertIn("lecturer", role_choices)


class RegistrationViewTests(TestCase):
    def setUp(self):
        self.url = reverse("register")
        self.valid_data = {
            "first_name": "Ada",
            "last_name": "Okafor",
            "email": "ada@example.com",
            "password": "SecurePass!927",
            "confirm_password": "SecurePass!927",
            "role": "student",
            "department": "Computer Science",
        }

    def test_get_displays_registration_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_valid_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(self.url, self.valid_data)

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(email="ada@example.com")
        self.assertEqual(user.username, "ada@example.com")
        self.assertEqual(user.first_name, "Ada")
        self.assertEqual(user.last_name, "Okafor")
        self.assertEqual(user.role, "student")
        self.assertEqual(user.department, "Computer Science")
        self.assertTrue(user.check_password("SecurePass!927"))

    def test_registration_rejects_mismatched_passwords(self):
        data = self.valid_data.copy()
        data["confirm_password"] = "DifferentPass!927"

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["error"], "Passwords do not match")
        self.assertFalse(User.objects.filter(email=data["email"]).exists())

    def test_registration_rejects_missing_required_fields(self):
        data = self.valid_data.copy()
        data["first_name"] = ""

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email=data["email"]).exists())

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username="ada@example.com",
            email="ada@example.com",
            password="ExistingPass!927",
            role="student",
        )

        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="ada@example.com").count(), 1)
