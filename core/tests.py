from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class DownloadPredictionsTests(TestCase):
    def setUp(self):
        User.objects.create_user("tester", password="pass12345!")
        self.client.login(username="tester", password="pass12345!")

    def test_no_analysis_redirects_to_history(self):
        response = self.client.get(reverse("download_predictions"))
        self.assertRedirects(response, reverse("prediction_history"))

class UploadAuthenticationTests(TestCase):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.post(
            reverse("upload_dataset")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)