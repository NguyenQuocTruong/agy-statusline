"""Payload parser for AGY statusline."""
import json
import sys
from typing import Dict, Any, Optional

# Sensitive keys to never expose or retain in output
SENSITIVE_KEYS = {
    "email", "access_token", "accessToken", "token", "password",
    "secret", "api_key", "apiKey", "authorization", "cookie"
}

def parse_payload(raw_input: Optional[str] = None) -> Dict[str, Any]:
    """Safely parse JSON payload from stdin or argument string."""
    if raw_input is None:
        try:
            raw_input = sys.stdin.read()
        except Exception:
            raw_input = ""

    if not raw_input or not raw_input.strip():
        return {}

    try:
        data = json.loads(raw_input)
        if not isinstance(data, dict):
            return {}
        return sanitize_payload(data)
    except Exception:
        return {}

def sanitize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize sensitive attributes from payload."""
    cleaned = {}
    for k, v in data.items():
        if k in SENSITIVE_KEYS:
            continue
        if isinstance(v, dict):
            cleaned[k] = sanitize_payload(v)
        elif isinstance(v, list):
            cleaned[k] = [sanitize_payload(item) if isinstance(item, dict) else item for item in v]
        else:
            cleaned[k] = v
    return cleaned
