from django.test import TestCase
from django.urls import reverse


class RegistrationTests(TestCase):
    def test_registration_with_missing_fields(self):
        response = self.client.post(
            reverse("register"),
            {}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_registration_with_weak_password(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "1",
                "confirm_password": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password")