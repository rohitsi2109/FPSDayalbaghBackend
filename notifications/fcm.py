# notifications/fcm.py
import json
import logging
import os
from typing import Iterable, Mapping
from firebase_admin import messaging, credentials, initialize_app
from firebase_admin._messaging_utils import UnregisteredError
from google.auth.exceptions import DefaultCredentialsError

log = logging.getLogger(__name__)

_initialized = False

def _init():
    """Initialize Firebase Admin exactly once, using env credentials."""
    global _initialized
    if _initialized:
        return
    try:
        cred = None

        # 1) Preferred: GOOGLE_APPLICATION_CREDENTIALS -> service account file path
        svc_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if svc_path and os.path.exists(svc_path):
            cred = credentials.Certificate(svc_path)

        # 2) Fallback: FIREBASE_CREDENTIALS_JSON -> raw JSON in an env var
        if not cred:
            raw = os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if raw:
                try:
                    data = json.loads(raw)
                    cred = credentials.Certificate(data)
                except Exception:
                    log.exception("Invalid FIREBASE_CREDENTIALS_JSON")

        # 3) Last resort: application default (often missing in serverless)
        if cred:
            initialize_app(cred)
        else:
            initialize_app()  # will use ADC if available

        _initialized = True
        log.info("Firebase Admin initialized for messaging.")
    except DefaultCredentialsError as e:
        log.error("Firebase Admin credentials not found: %s", e)
        raise
    except Exception:
        log.exception("Firebase Admin init failed")
        raise

def send_to_tokens(
    tokens: Iterable[str],
    title: str,
    body: str,
    data: Mapping[str, str] | None = None,
):
    _init()
    tokens = [t for t in tokens if t]
    if not tokens:
        return {"success": 0, "failure": 0, "errors": []}

    msg = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(payload=messaging.APNSPayload()),
    )

    resp = messaging.send_each_for_multicast(msg)
    # Detailed logging (helps catch MISMATCH_SENDER_ID / UNREGISTERED)
    errors = []
    for i, r in enumerate(resp.responses):
        if not r.success:
            err = getattr(r.exception, "code", str(r.exception))
            errors.append({"token": tokens[i], "error": err})
    log.info("FCM sent: success=%s failure=%s errors=%s",
             resp.success_count, resp.failure_count, errors)
    return {"success": resp.success_count, "failure": resp.failure_count, "errors": errors}
