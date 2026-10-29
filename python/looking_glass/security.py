"""Password hashing and token helpers (stdlib only: hashlib.scrypt)."""

import base64
import hashlib
import hmac
import secrets
import threading
import time

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32)
    b64 = lambda b: base64.b64encode(b).decode()
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${b64(salt)}${b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_b64, dk_b64 = stored.split("$")
        if algo != "scrypt":
            return False
        expected = base64.b64decode(dk_b64)
        dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64),
                            n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(dk, expected)
    except (ValueError, TypeError):
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    """Session tokens are stored hashed so a DB leak does not leak live sessions."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_password(length: int = 16) -> str:
    return secrets.token_urlsafe(length)[:length]


def constant_eq(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return hmac.compare_digest(a.encode(), b.encode())


class LoginThrottle:
    """Process-local rolling-window throttle with bounded failure retention.

    Saturation denies untracked keys rather than evicting active histories.
    Checks do not reserve capacity: authentication already in flight can finish
    after capacity fills, in which case fail() cannot allocate another key.
    """

    MAX_KEYS = 4096

    def __init__(self, max_failures: int, lockout_seconds: int):
        self.max_failures = max_failures
        self.lockout = lockout_seconds
        self._fails: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _key(self, ip: str, username: str) -> str:
        return f"{ip}|{username.lower()}"

    def _prune(self, now: float) -> None:
        # Called only while holding _lock; includes abandoned keys.
        for key in list(self._fails):
            hits = [t for t in self._fails[key] if now - t < self.lockout]
            if hits:
                self._fails[key] = hits
            else:
                del self._fails[key]

    def blocked(self, ip: str, username: str) -> bool:
        with self._lock:
            self._prune(time.monotonic())
            hits = self._fails.get(self._key(ip, username), [])
            return (len(hits) >= self.max_failures or
                    (not hits and len(self._fails) >= self.MAX_KEYS))

    def fail(self, ip: str, username: str) -> None:
        with self._lock:
            now = time.monotonic()
            self._prune(now)
            if self.max_failures <= 0 or self.lockout <= 0:
                return
            key = self._key(ip, username)
            if key not in self._fails:
                if len(self._fails) >= self.MAX_KEYS:
                    return
                self._fails[key] = []
            hits = self._fails[key]
            hits.append(now)
            del hits[:-self.max_failures]

    def reset(self, ip: str, username: str) -> None:
        with self._lock:
            self._fails.pop(self._key(ip, username), None)
