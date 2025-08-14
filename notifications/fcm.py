import logging
from typing import Iterable, Mapping
from firebase_admin import messaging, credentials, initialize_app
from django.conf import settings

log = logging.getLogger(__name__)

# Initialize Firebase Admin once.
_initialized = False
def _init():
    global _initialized
    if _initialized:
        return
    # You can use GOOGLE_APPLICATION_CREDENTIALS env var, or path in settings
    # Example: settings.FIREBASE_CREDENTIALS_FILE = BASE_DIR / "service-account.json"
    cred = None
    if getattr(settings, "FIREBASE_CREDENTIALS_FILE", None):
        cred = credentials.Certificate(str(settings.FIREBASE_CREDENTIALS_FILE))
        initialize_app(cred)
    else:
        # Falls back to default credentials (works if env var GOOGLE_APPLICATION_CREDENTIALS is set)
        initialize_app()
    _initialized = True

def send_to_tokens(
    tokens: Iterable[str],
    title: str,
    body: str,
    data: Mapping[str, str] | None = None,
):
    _init()
    tokens = [t for t in tokens if t]
    if not tokens:
        return

    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(payload=messaging.APNSPayload()),
    )
    resp = messaging.send_each_for_multicast(message)
    log.info("FCM sent: success=%s failure=%s", resp.success_count, resp.failure_count)
