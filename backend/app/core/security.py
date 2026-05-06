from __future__ import annotations

import hashlib
import hmac
import secrets

_PBKDF2_ITERATIONS = 200_000
_SALT_BYTES = 16


def get_password_hash(password: str) -> str:
    """Return a salted PBKDF2 hash in ``salt$hash`` format."""
    salt = secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        _PBKDF2_ITERATIONS,
    ).hex()
    return f"{salt}${digest}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a salted PBKDF2 hash."""
    try:
        salt, stored_digest = hashed_password.split("$", 1)
        expected = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            bytes.fromhex(salt),
            _PBKDF2_ITERATIONS,
        ).hex()
        return hmac.compare_digest(expected, stored_digest)
    except (ValueError, TypeError):
        return False
