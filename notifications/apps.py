from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    name = 'notifications'
    verbose_name = 'Notifications'

    def ready(self):
        # Ensure firebase is initialized on startup
        from . import firebase_init  # noqa
