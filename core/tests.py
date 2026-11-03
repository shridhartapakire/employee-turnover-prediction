
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from core.models import AnalysisResult


class DownloadPredictionsTests(TestCase):
    def setUp(self):
        User.objects.create_user("tester", password="pass12345!")
        self.client.login(username="tester", password="pass12345!")

    def test_no_analysis_redirects_to_history(self):
        response = self.client.get(reverse("download_predictions"))
        self.assertRedirects(response, reverse("prediction_history"))


class UploadAuthenticationTests(TestCase):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.post(reverse("upload_dataset"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


class DatasetDownloadSecurityTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            password="pass12345!"
        )
        self.user2 = User.objects.create_user(
            username="user2",
            password="pass12345!"
        )

        uploaded_file = SimpleUploadedFile(
            "test_dataset.csv",
            b"Age,left\n30,0\n40,1\n",
            content_type="text/csv",
        )

        self.analysis = AnalysisResult.objects.create(
            user=self.user1,
            upload_filename="test_dataset.csv",
            uploaded_file=uploaded_file,
            total_employees=2,
            predicted_turnover_count=1,
        )

        self.download_url = reverse(
            "download_uploaded_dataset",
            args=[self.analysis.id],
        )

    def test_owner_can_download_own_dataset(self):
        self.client.login(username="user1", password="pass12345!")
        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="test_dataset.csv"',
        )
        response.close()

    def test_other_user_cannot_download_dataset(self):
        self.client.login(username="user2", password="pass12345!")
        response = self.client.get(self.download_url)

        self.assertRedirects(
            response,
            reverse("prediction_history"),
        )
        response.close()

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_missing_dataset_is_handled_safely(self):
        self.client.login(username="user1", password="pass12345!")

        response = self.client.get(
            reverse("download_uploaded_dataset", args=[99999])
        )

        self.assertRedirects(
            response,
            reverse("prediction_history"),
        )
