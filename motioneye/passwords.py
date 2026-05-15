"""Password hashing and verification for motionEye.

Uses bcrypt for password storage. A separate `compute_sig_key` helper
returns the SHA-1 of the password — used as the HMAC key for the
existing client-side signature flow, which cannot be changed without
also rewriting the JS client (see follow-up task).

Legacy SHA-1 hashes (40 hex chars) are recognized and verified for
backward compatibility with deployments not yet migrated.
"""
import hashlib
import hmac
import re

import bcrypt

_SHA1_HEX_RE = re.compile(r'^[0-9a-f]{40}$')


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt. Empty input → empty output."""
    if password == '':
        return ''
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def is_legacy_hash(stored: str) -> bool:
    """Return True if the stored hash is a legacy SHA-1 hex digest."""
    return bool(stored) and bool(_SHA1_HEX_RE.match(stored))


def verify_password(submitted: str, stored: str) -> bool:
    """Constant-time verify of a submitted password against stored hash.

    - Empty stored => no password required (returns True only for empty submitted).
    - Legacy SHA-1 stored => SHA-1 hash check (constant-time).
    - bcrypt stored => bcrypt check.
    """
    if stored == '':
        return submitted == ''
    if is_legacy_hash(stored):
        candidate = hashlib.sha1(submitted.encode('utf-8')).hexdigest()
        return hmac.compare_digest(candidate, stored)
    try:
        return bcrypt.checkpw(submitted.encode('utf-8'), stored.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def compute_sig_key(password: str) -> str:
    """Return the HMAC signature key for `password`.

    Currently sha1(password) for backward compat with the JS client's
    signature contract. Stored in `@*_password_sig_key` config fields.
    """
    if password == '':
        return ''
    return hashlib.sha1(password.encode('utf-8')).hexdigest()
