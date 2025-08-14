import logging
from typing import Iterable, Dict, Any

logger = logging.getLogger(__name__)

def send_fcm_multicast(tokens: Iterable[str], title: str, body: str, data: Dict[str, Any] | None = None):
    try:
        from firebase_admin import messaging
    except Exception:
        logger.warning("Firebase not initialized; skipping push.")
        return

    tokens = [t for t in tokens if t]
    if not tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        tokens=tokens,
        android=messaging.AndroidConfig(priority='high'),
        apns=messaging.APNSConfig(headers={'apns-priority': '10'}),
    )
    try:
        resp = messaging.send_multicast(message)
        logger.info("FCM multicast sent: success=%s failure=%s", resp.success_count, resp.failure_count)
    except Exception as e:
        logger.exception("FCM send failed: %s", e)
