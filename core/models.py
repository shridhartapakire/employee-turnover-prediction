from django.db import models
from django.contrib.auth.models import User


class AnalysisResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_filename = models.CharField(max_length=255)
    analysis_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.upload_filename} - {self.user.username}"

    class Meta:
        ordering = ["-analysis_date"]