from django.db import models
from django.conf import settings

class Device(models.Model):
    ANDROID = 'android'
    IOS = 'ios'
    WEB = 'web'
    PLATFORM_CHOICES = [(ANDROID, 'Android'), (IOS, 'iOS'), (WEB, 'Web')]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='devices',
        null=True, blank=True
    )
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default=ANDROID)
    is_active = models.BooleanField(default=True)

    # Mark shopkeeper devices (the people who should get “new order” notifications)
    is_admin_receiver = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.user.phone if self.user else 'anon'
        return f'{who} [{self.platform}]'
