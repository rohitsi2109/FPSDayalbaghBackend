# # notifications/fcm.py
# import logging
# from pathlib import Path
# from typing import Iterable, Mapping
#
# from django.conf import settings
# import firebase_admin
# from firebase_admin import credentials, messaging
#
# log = logging.getLogger(__name__)
#
# def _init():
#     """Initialize Firebase Admin once using local firebase-admin.json + explicit projectId."""
#     if firebase_admin._apps:
#         return firebase_admin.get_app()
#
#     cred_path = Path(getattr(
#         settings, "FIREBASE_ADMIN_CREDENTIALS_FILE",
#         Path(settings.BASE_DIR) / "firebase-admin.json"
#     ))
#     project_id = getattr(settings, "FIREBASE_PROJECT_ID", None)
#
#     if cred_path.exists():
#         cred = credentials.Certificate(str(cred_path))
#         return firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
#
#     # Fallback (not recommended, but keeps the code robust)
#     return firebase_admin.initialize_app(options={"projectId": project_id} if project_id else None)
#
# def _send_one(token: str, title: str, body: str, data: Mapping[str, str] | None, app):
#     msg = messaging.Message(
#         token=token,
#         notification=messaging.Notification(title=title, body=body),
#         data={k: str(v) for k, v in (data or {}).items()},
#         android=messaging.AndroidConfig(priority="high"),
#         # Add APNS config later if/when you support iOS
#     )
#     try:
#         messaging.send(msg, app=app)
#         return True, None
#     except Exception as exc:
#         code = getattr(exc, "code", "")
#         message = getattr(exc, "message", str(exc))
#         return False, {"token": token, "code": code, "message": message}
#
# def send_to_tokens(
#     tokens: Iterable[str],
#     title: str,
#     body: str,
#     data: Mapping[str, str] | None = None,
# ):
#     app = _init()
#
#     clean_tokens = [t for t in tokens if t]
#     if not clean_tokens:
#         return {"success": 0, "failure": 0, "errors": [], "removed": 0}
#
#     success = 0
#     errors = []
#     removed = 0
#
#     for t in clean_tokens:
#         ok, err = _send_one(t, title, body, data, app)
#         if ok:
#             success += 1
#         else:
#             errors.append(err)
#             # Clean up obviously dead tokens if you want
#             if str(err.get("code", "")).upper() in {"UNREGISTERED", "INVALID_ARGUMENT"}:
#                 removed += 1
#
#     log.info("FCM (per-token): success=%s failure=%s errors=%s", success, len(errors), errors)
#     return {"success": success, "failure": len(errors), "errors": errors, "removed": removed}
#



# notifications/fcm.py
import json
import logging
import os
from pathlib import Path
from typing import Iterable, Mapping

from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging

log = logging.getLogger(__name__)

def _init():
    """
    Initialize Firebase Admin once.

    Order of credential sources:
    1) FIREBASE_CREDENTIALS_JSON (raw JSON in env)  <-- use this on Vercel
    2) settings.FIREBASE_ADMIN_CREDENTIALS_FILE (local file path)
       (defaults to BASE_DIR/firebase-admin.json)
    3) GOOGLE_APPLICATION_CREDENTIALS (file path in env)
    4) options-only init (projectId from env/settings), as a last resort
    """
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred = None

    # 1) Vercel-friendly: paste raw JSON into env var
    raw = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if raw:
        try:
            data = json.loads(raw)
            cred = credentials.Certificate(data)
        except Exception:
            log.exception("FIREBASE_CREDENTIALS_JSON is not valid JSON")

    # 2) Local file (your current local setup)
    if cred is None:
        cred_path = Path(getattr(
            settings, "FIREBASE_ADMIN_CREDENTIALS_FILE",
            Path(settings.BASE_DIR) / "firebase-admin.json"
        ))
        if cred_path.exists():
            cred = credentials.Certificate(str(cred_path))

    # 3) Standard GAC file path (optional)
    if cred is None:
        gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if gac and Path(gac).exists():
            cred = credentials.Certificate(gac)

    # 4) Initialize
    if cred is not None:
        app = firebase_admin.initialize_app(cred)
        log.info("Firebase Admin initialized with service account.")
        return app

    # Last-resort: options-only init (works if projectId is discoverable)
    project_id = (
        os.environ.get("FIREBASE_PROJECT_ID")
        or getattr(settings, "FIREBASE_PROJECT_ID", None)
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCLOUD_PROJECT")
    )
    opts = {"projectId": project_id} if project_id else None
    app = firebase_admin.initialize_app(options=opts)
    log.info("Firebase Admin initialized without explicit credentials%s",
             f" (project_id={project_id})" if project_id else "")
    return app


def _send_one(token: str, title: str, body: str, data: Mapping[str, str] | None, app):
    msg = messaging.Message(
        token=token,
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        android=messaging.AndroidConfig(priority="high"),
        # Add APNS config later if/when you support iOS
    )
    try:
        messaging.send(msg, app=app)
        return True, None
    except Exception as exc:
        code = getattr(exc, "code", "") or getattr(exc, "detail", "")
        message = getattr(exc, "message", None) or str(exc)
        return False, {"token": token, "code": code, "message": message}


def send_to_tokens(
    tokens: Iterable[str],
    title: str,
    body: str,
    data: Mapping[str, str] | None = None,
):
    app = _init()

    clean_tokens = [t for t in tokens if t]
    if not clean_tokens:
        return {"success": 0, "failure": 0, "errors": [], "removed": 0}

    success = 0
    errors = []
    removed = 0

    # Send per-token (avoids /batch issues in some serverless envs)
    for t in clean_tokens:
        ok, err = _send_one(t, title, body, data, app)
        if ok:
            success += 1
        else:
            errors.append(err)
            if str(err.get("code", "")).upper() in {"UNREGISTERED", "INVALID_ARGUMENT"}:
                removed += 1

    log.info("FCM (per-token): success=%s failure=%s errors=%s", success, len(errors), errors)
    return {"success": success, "failure": len(errors), "errors": errors, "removed": removed}
