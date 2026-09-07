from django.db import models
from django.contrib.auth.models import User


class AnalysisResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_filename = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to="datasets/", blank=True, null=True)
    
    predicted_turnover_count = models.PositiveIntegerField(default=0)
    average_turnover_probability = models.FloatField(default=0.0)

    analysis_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.upload_filename} - {self.user.username}"

    class Meta:
        ordering = ["-analysis_date"]