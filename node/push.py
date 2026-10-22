"""
APNs push notification sender.

Config via env vars:
  APNS_KEY_ID      — Key ID from Apple Developer portal
  APNS_TEAM_ID     — Team ID (e.g. EHL866FYNR)
  APNS_BUNDLE_ID   — Bundle ID (e.g. com.avk.Nevod)
  APNS_PRIVATE_KEY — .p8 key contents (or path to .p8 file)
  APNS_SANDBOX     — "true" for dev/sandbox, "false" for production (default: true)
"""

import logging
import os
import time

log = logging.getLogger(__name__)

try:
    import jwt as _jwt
    _HAS_JWT = True
except ImportError:
    _HAS_JWT = False
    log.warning("PyJWT not installed — push notifications disabled. Run: pip install PyJWT")

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False
    log.warning("httpx not installed — push notifications disabled. Run: pip install 'httpx[http2]'")

APNS_HOST_SANDBOX = "https://api.sandbox.push.apple.com"
APNS_HOST_PROD    = "https://api.push.apple.com"
_TOKEN_TTL = 3000  # refresh JWT every 50 minutes (APNs max is 60)


class APNsSender:
    def __init__(self, key_id: str, team_id: str, private_key: str,
                 bundle_id: str, sandbox: bool = True):
        self._key_id = key_id
        self._team_id = team_id
        self._private_key = private_key
        self._bundle_id = bundle_id
        self._host = APNS_HOST_SANDBOX if sandbox else APNS_HOST_PROD
        self._jwt: str | None = None
        self._jwt_ts: float = 0
        self._client: "httpx.AsyncClient | None" = None

    def _make_jwt(self) -> str:
        now = time.time()
        if self._jwt and now - self._jwt_ts < _TOKEN_TTL:
            return self._jwt
        self._jwt = _jwt.encode(
            {"iss": self._team_id, "iat": int(now)},
            self._private_key,
            algorithm="ES256",
            headers={"kid": self._key_id},
        )
        self._jwt_ts = now
        return self._jwt

    async def _client_(self) -> "httpx.AsyncClient":
        if self._client is None:
            self._client = httpx.AsyncClient(http2=True)
        return self._client

    async def send(self, device_token: str, title: str, body: str, badge: int = 1,
                    sound: bool = True, sender_cell_id: str = "") -> bool:
        if not (_HAS_JWT and _HAS_HTTPX):
            return False
        try:
            client = await self._client_()
            # mutable-content lets the iOS Notification Service Extension rewrite the alert
            # before it's shown — specifically to swap this generic title for the recipient's
            # own local contact alias, which the node can never know (that's private,
            # client-side-only data — see NotificationService/NotificationService.swift).
            aps: dict = {"alert": {"title": title, "body": body}, "badge": badge,
                        "mutable-content": 1}
            if sound:
                aps["sound"] = "default"
            # sender_cell_id lives outside "aps" (standard APNs custom-data placement) —
            # the iOS client reads it from the notification's userInfo on tap to deep-link
            # straight into the right chat instead of just opening to whatever screen was
            # last shown (see NevdApp.swift's UNUserNotificationCenterDelegate).
            payload: dict = {"aps": aps}
            if sender_cell_id:
                payload["sender_cell_id"] = sender_cell_id
            resp = await client.post(
                f"{self._host}/3/device/{device_token}",
                json=payload,
                headers={
                    "authorization": f"bearer {self._make_jwt()}",
                    "apns-topic": self._bundle_id,
                    "apns-push-type": "alert",
                    "apns-priority": "10",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                log.debug("push sent to %s…", device_token[:8])
                return True
            log.warning("APNs %d: %s", resp.status_code, resp.text[:200])
            return False
        except Exception as e:
            log.error("APNs send error: %s", e)
            return False

    async def send_voip(self, device_token: str, caller_id: str, caller_name: str) -> bool:
        """VoIP push — wakes the app even if fully killed, so it can call
        CXProvider.reportNewIncomingCall. No visible alert: CallKit shows its own UI."""
        if not (_HAS_JWT and _HAS_HTTPX):
            return False
        try:
            client = await self._client_()
            resp = await client.post(
                f"{self._host}/3/device/{device_token}",
                json={"aps": {}, "caller_id": caller_id, "caller_name": caller_name},
                headers={
                    "authorization": f"bearer {self._make_jwt()}",
                    "apns-topic": f"{self._bundle_id}.voip",
                    "apns-push-type": "voip",
                    "apns-priority": "10",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                log.debug("voip push sent to %s…", device_token[:8])
                return True
            log.warning("APNs voip %d: %s", resp.status_code, resp.text[:200])
            return False
        except Exception as e:
            log.error("APNs voip send error: %s", e)
            return False

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


def from_env() -> "APNsSender | None":
    """Create APNsSender from environment variables. Returns None if not configured."""
    key_id  = os.getenv("APNS_KEY_ID", "")
    team_id = os.getenv("APNS_TEAM_ID", "")
    bundle  = os.getenv("APNS_BUNDLE_ID", "com.avk.Nevod")
    sandbox = os.getenv("APNS_SANDBOX", "true").lower() != "false"

    raw_key = os.getenv("APNS_PRIVATE_KEY", "")
    if not raw_key:
        return None  # push not configured
    # allow path to .p8 file
    if not raw_key.startswith("-----") and os.path.isfile(raw_key):
        with open(raw_key) as f:
            raw_key = f.read()

    if not (key_id and team_id and raw_key):
        return None

    return APNsSender(key_id, team_id, raw_key, bundle, sandbox)
