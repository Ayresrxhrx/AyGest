from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone


def generate_activation_key() -> str:
    parts = [secrets.token_hex(2).upper(), secrets.token_hex(2).upper(), secrets.token_hex(2).upper(), secrets.token_hex(2).upper()]
    return "AYG-" + "-".join(parts)


def fingerprint(payload: dict, secret: str) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


def build_offline_license(payload: dict, secret: str) -> str:
    body = dict(payload)
    body["issued_at"] = datetime.now(timezone.utc).isoformat()
    body["signature"] = fingerprint(body, secret)
    encoded = base64.urlsafe_b64encode(json.dumps(body, separators=(",", ":")).encode()).decode()
    return encoded.rstrip("=")


def verify_offline_license(token: str, secret: str) -> dict | None:
    try:
        padded = token + "=" * (-len(token) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        signature = payload.pop("signature")
        if not hmac.compare_digest(signature, fingerprint(payload, secret)):
            return None
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
