from django.db import models


class ManagementAuthToken(models.Model):
    """Server-side storage for administrator API authentication."""

    session_key = models.CharField(
        max_length=40,
        unique=True,
        db_index=True,
    )

    encrypted_access_token = models.TextField()

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Management authentication token"
        verbose_name_plural = "Management authentication tokens"

    def __str__(self):
        return f"Management session {self.pk}"
