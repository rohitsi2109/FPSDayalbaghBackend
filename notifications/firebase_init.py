import os
import logging

logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials

    if not firebase_admin._apps:
        cred = None
        # Preferred: GOOGLE_APPLICATION_CREDENTIALS path
        svc_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if svc_path and os.path.exists(svc_path):
            cred = credentials.Certificate(svc_path)

        # Fallback: FIREBASE_CREDENTIALS_JSON env with JSON string
        if not cred:
            json_str = os.environ.get('FIREBASE_CREDENTIALS_JSON')
            if json_str:
                import json, tempfile
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                tmp.write(json_str.encode('utf-8'))
                tmp.flush()
                cred = credentials.Certificate(tmp.name)

        if cred:
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized.")
        else:
            logger.warning("Firebase credentials not provided; notifications disabled.")
except Exception as e:
    logger.exception("Firebase init failed: %s", e)
