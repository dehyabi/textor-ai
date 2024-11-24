from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.

class Transcription(models.Model):
    transcript_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    text = models.TextField(null=True, blank=True)
    audio_url = models.URLField()
    language_code = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Transcription {self.transcript_id} ({self.status})"
