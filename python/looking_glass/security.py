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
    """Tiny in-memory brute-force throttle keyed by (ip, username)."""

    def __init__(self, max_failures: int, lockout_seconds: int):
        self.max_failures = max_failures
        self.lockout = lockout_seconds
        self._fails: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _key(self, ip: str, username: str) -> str:
        return f"{ip}|{username.lower()}"

    def blocked(self, ip: str, username: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = [t for t in self._fails.get(self._key(ip, username), []) if now - t < self.lockout]
            self._fails[self._key(ip, username)] = hits
            return len(hits) >= self.max_failures

    def fail(self, ip: str, username: str) -> None:
        with self._lock:
            self._fails.setdefault(self._key(ip, username), []).append(time.monotonic())

    def reset(self, ip: str, username: str) -> None:
        with self._lock:
            self._fails.pop(self._key(ip, username), None)
