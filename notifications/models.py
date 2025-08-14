from django.conf import settings
from django.db import models

class Device(models.Model):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    PLATFORM_CHOICES = (
        (ANDROID, "Android"),
        (IOS, "iOS"),
        (WEB, "Web"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
        null=True,
        blank=True,
    )
    token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(max_length=16, choices=PLATFORM_CHOICES, default=ANDROID)
    is_admin = models.BooleanField(default=False)  # shopkeeper devices
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        who = self.user_id or "anon"
        return f"{self.platform}:{self.token[:16]}…(user={who}, admin={self.is_admin})"
