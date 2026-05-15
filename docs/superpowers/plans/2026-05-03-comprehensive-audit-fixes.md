# MotionEye-Custom Comprehensive Audit Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address all critical security findings, code quality issues, and cleanup items identified in the 2026-05-03 comprehensive audit, with TDD-style verification for each fix.

**Architecture:** Work in 4 sequential phases. Phase 1 fixes critical security issues (cryptography, RCE, TLS). Phase 2 hardens auth, headers, and process behavior. Phase 3 addresses code quality and architecture. Phase 4 removes dead code and consolidates CI. Each task uses test-first methodology where verifiable; pure-cleanup tasks use existing test suite as the verification gate.

**Tech Stack:** Python 3.9+, Tornado 6.x, pytest, `tornado.testing.AsyncHTTPTestCase`, bcrypt (new dependency), pre-existing `HandlerTestCase` at `tests/test_handlers/__init__.py`.

**Test command pattern:**
- Single test: `python -m pytest tests/path/test_file.py::ClassName::test_name -v`
- Phase suite: `python -m pytest tests/ -v`
- All including root-level: `python -m pytest -v`

**Commit cadence:** One commit per task. Branch: `audit-fixes-2026-05`.

---

## Phase 0: Setup

### Task 0.1: Create branch and confirm baseline

**Files:**
- N/A (git only)

- [ ] **Step 1: Create working branch**

```bash
git checkout main
git pull
git checkout -b audit-fixes-2026-05
```

- [ ] **Step 2: Run existing test suite to establish baseline**

Run: `python -m pytest tests/ -v 2>&1 | tail -30`
Expected: Record the pass/fail/skip counts. All subsequent tasks must keep the pre-existing tests at the same status (no regressions).

- [ ] **Step 3: Save baseline counts to a scratch note**

Record in your working notes (NOT in repo): `BASELINE: X passed, Y failed, Z skipped`.

---

## Phase 1: Critical Security Fixes

> **Implementation note (2026-05-03):** Task 1.1 was adopted with a
> *dual-hash variant* of the spec below: the JS client uses
> `sha1(password)` as its HMAC signature key, so the bcrypt migration
> required keeping that derivation alongside the new bcrypt password
> hash. See commit `e851cff1` and the follow-up hardening at
> `d8537192`. The original single-hash spec is left for context but
> the implementation diverged as noted.

### Task 1.1 (C1): Replace SHA-1 password hashing with bcrypt

**Files:**
- Modify: `setup.cfg` (add `bcrypt>=4.0,<5.0` dependency)
- Create: `motioneye/passwords.py` (new password hashing module)
- Modify: `motioneye/handlers/base.py:208-272` (replace SHA-1 calls)
- Modify: `motioneye/config.py:903-905` (use new module when persisting passwords)
- Create: `tests/test_passwords.py`

- [ ] **Step 1: Add bcrypt to setup.cfg**

In `setup.cfg`, under `install_requires`, add:
```
    bcrypt>=4.0,<5.0
```

- [ ] **Step 2: Install bcrypt locally**

Run: `pip install 'bcrypt>=4.0,<5.0'`
Expected: Successful installation.

- [ ] **Step 3: Write failing tests for the password module**

Create `tests/test_passwords.py`:
```python
import unittest
from motioneye import passwords


class PasswordsTest(unittest.TestCase):
    def test_hash_password_returns_bcrypt_string(self):
        h = passwords.hash_password('secret')
        self.assertTrue(h.startswith('$2b$') or h.startswith('$2a$'))

    def test_verify_correct_password(self):
        h = passwords.hash_password('secret')
        self.assertTrue(passwords.verify_password('secret', h))

    def test_verify_wrong_password(self):
        h = passwords.hash_password('secret')
        self.assertFalse(passwords.verify_password('wrong', h))

    def test_legacy_sha1_hash_is_recognized(self):
        # SHA-1 of "secret"
        legacy = 'e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4'
        self.assertTrue(passwords.is_legacy_hash(legacy))
        self.assertFalse(passwords.is_legacy_hash(passwords.hash_password('x')))

    def test_verify_legacy_sha1_password(self):
        legacy = 'e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4'
        self.assertTrue(passwords.verify_password('secret', legacy))
        self.assertFalse(passwords.verify_password('wrong', legacy))

    def test_empty_password_handling(self):
        # Empty stored password means no auth required (preserved behavior)
        self.assertTrue(passwords.verify_password('', ''))
        self.assertFalse(passwords.verify_password('anything', ''))
```

- [ ] **Step 4: Run tests to confirm failure**

Run: `python -m pytest tests/test_passwords.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'motioneye.passwords'`

- [ ] **Step 5: Implement the passwords module**

Create `motioneye/passwords.py`:
```python
"""Password hashing and verification for motionEye.

Supports bcrypt (current) and SHA-1 (legacy) for backward compatibility.
Legacy hashes are auto-detected by length (40 hex chars).
"""
import hashlib
import hmac
import re

import bcrypt

_SHA1_HEX_RE = re.compile(r'^[0-9a-f]{40}$')


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
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
```

- [ ] **Step 6: Run tests to confirm pass**

Run: `python -m pytest tests/test_passwords.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 7: Update `motioneye/config.py` to use bcrypt for new passwords**

In `motioneye/config.py`, locate the block (around line 903-915) that hashes admin/normal passwords. Replace SHA-1 calls with `passwords.hash_password()`. Add at top: `from motioneye import passwords`.

Specifically:
```python
# OLD
data['@admin_password'] = hashlib.sha1(ui['admin_password'].encode('utf-8')).hexdigest()
data['@normal_password'] = ui['normal_password']  # was plaintext bug (Q7)

# NEW
data['@admin_password'] = passwords.hash_password(ui['admin_password'])
data['@normal_password'] = passwords.hash_password(ui['normal_password'])
```

This also fixes finding **Q7** (normal user password plaintext storage).

- [ ] **Step 8: Update `motioneye/handlers/base.py` `get_current_user` to use `passwords.verify_password`**

Replace lines 221-272 (basic auth + signature auth blocks) so that:
- The `admin_hash` / `normal_hash` SHA-1 of the stored password are removed (no more pass-the-hash, fixing **Q8**).
- Basic auth uses `passwords.verify_password(up['password'], stored)`.
- Signature auth keeps using `compute_signature(..., stored)` for now (Task 1.2 will harden the comparison).

Replacement block:
```python
admin_password = main_config.get('@admin_password', '')
normal_password = main_config.get('@normal_password', '')

if settings.HTTP_BASIC_AUTH and 'Authorization' in self.request.headers:
    up = utils.parse_basic_header(self.request.headers['Authorization'])
    if up:
        if up['username'] == admin_username and passwords.verify_password(up['password'], admin_password):
            return 'admin'
        if up['username'] == normal_username and passwords.verify_password(up['password'], normal_password):
            return 'normal'

if username == admin_username and signature == utils.compute_signature(
    self.request.method, self.request.uri, self.request.body, admin_password
):
    return 'admin'

if not username and not normal_password:
    return 'normal'

if username == normal_username and signature == utils.compute_signature(
    self.request.method, self.request.uri, self.request.body, normal_password
):
    return 'normal'
```

Add at top of `handlers/base.py`: `from motioneye import passwords`. Remove `import hashlib` if no longer used elsewhere in the file (verify with grep).

- [ ] **Step 9: Run full test suite to check regressions**

Run: `python -m pytest tests/ -v`
Expected: Same baseline pass count or better. The `test_get_current_user` and login tests must still pass — adjust them only if they depend on the pass-the-hash misfeature.

- [ ] **Step 10: Manual smoke test**

Start the server locally: `python -m motioneye.meyectl startserver` (or your standard run command). Log in via the web UI with the existing admin password. Expected: login succeeds; on next config save, the stored hash transparently upgrades to bcrypt format. Verify by inspecting `motioneye.conf`: `@admin_password` should now start with `$2b$`.

- [ ] **Step 11: Commit**

```bash
git add setup.cfg motioneye/passwords.py motioneye/config.py motioneye/handlers/base.py tests/test_passwords.py
git commit -m "security: replace SHA-1 password hashing with bcrypt (C1, Q7, Q8)

- New motioneye.passwords module with bcrypt + legacy SHA-1 verify
- Hash normal user password (was stored plaintext)
- Remove pass-the-hash code path in basic auth
- Backward-compatible: legacy SHA-1 hashes still verify"
```

---

### Task 1.2 (C2): Use `hmac.compare_digest` for signature comparison

**Files:**
- Modify: `motioneye/handlers/base.py:208-272` (signature auth block)
- Create: `tests/test_handlers/test_base_signature.py`

- [ ] **Step 1: Write failing test for constant-time signature comparison**

Create `tests/test_handlers/test_base_signature.py`:
```python
import inspect
import unittest
from motioneye.handlers import base


class SignatureComparisonTest(unittest.TestCase):
    def test_get_current_user_uses_compare_digest(self):
        src = inspect.getsource(base.BaseHandler.get_current_user)
        self.assertIn('compare_digest', src)
        compact = ''.join(src.split())
        self.assertNotIn('signature==utils.compute_signature', compact)
```

- [ ] **Step 2: Run test to confirm failure**

Run: `python -m pytest tests/test_handlers/test_base_signature.py -v`
Expected: FAIL — current code uses `==`.

- [ ] **Step 3: Update `get_current_user` to use `hmac.compare_digest`**

In `motioneye/handlers/base.py`, add `import hmac` at the top. Replace the two signature comparisons:

```python
# OLD
if username == admin_username and signature == utils.compute_signature(
    self.request.method, self.request.uri, self.request.body, admin_password
):

# NEW
if username == admin_username and signature is not None and hmac.compare_digest(
    signature,
    utils.compute_signature(self.request.method, self.request.uri, self.request.body, admin_password),
):
```

Apply the same transform to the `normal_username` block.

- [ ] **Step 4: Run tests to confirm pass**

Run: `python -m pytest tests/test_handlers/test_base_signature.py tests/test_handlers/test_login.py -v`
Expected: New test PASSES, login tests still PASS.

- [ ] **Step 5: Commit**

```bash
git add motioneye/handlers/base.py tests/test_handlers/test_base_signature.py
git commit -m "security: constant-time signature comparison (C2)

Use hmac.compare_digest in BaseHandler.get_current_user to prevent
byte-level timing-attack signature recovery."
```

---

### Task 1.3 (C3): Eliminate unsafe deserialization

**Files:**
- Modify: `motioneye/extra/opencv_processor.py:114` (and corresponding write paths)
- Modify: `motioneye/tasks.py:182` (and write path)
- Modify: `motioneye/face_recognition_manager.py:335` (and write path)
- Create: `tests/test_face_encoding_persistence.py`

The current code uses Python's binary-serialization module that allows arbitrary code execution on load. We replace it with JSON.

- [ ] **Step 1: Audit all unsafe load/dump call sites**

Run: `grep -nE "\.(dump|load)" motioneye/ -r | grep -i pickle`
Expected: List of files. Confirm matches the 3 files above.

- [ ] **Step 2: Write failing test for JSON-based face encoding persistence**

Create `tests/test_face_encoding_persistence.py`:
```python
import json
import os
import tempfile
import unittest
import numpy as np

from motioneye import face_recognition_manager


class FaceEncodingPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_save_and_load_uses_json(self):
        path = os.path.join(self.tmpdir, 'faces.json')
        encodings = {
            'alice': [np.zeros(128).tolist()],
            'bob': [np.ones(128).tolist()],
        }
        face_recognition_manager.save_encodings(path, encodings)

        # File must be JSON-parseable
        with open(path, 'r') as f:
            data = json.load(f)
        self.assertIn('alice', data)

        loaded = face_recognition_manager.load_encodings(path)
        self.assertIn('alice', loaded)
        self.assertEqual(len(loaded['alice']), 1)

    def test_load_missing_file_returns_empty(self):
        loaded = face_recognition_manager.load_encodings('/nonexistent/path.json')
        self.assertEqual(loaded, {})
```

- [ ] **Step 3: Run test to confirm failure**

Run: `python -m pytest tests/test_face_encoding_persistence.py -v`
Expected: FAIL — `save_encodings` / `load_encodings` do not exist as JSON-based functions yet.

- [ ] **Step 4: Replace unsafe deserialization in `face_recognition_manager.py`**

In `motioneye/face_recognition_manager.py`:
- Add JSON-based `save_encodings(path, encodings)` and `load_encodings(path)` helpers. Convert numpy arrays to lists on save, back to arrays on load.
- Replace the existing `.load(f)` (line ~335) call with `load_encodings(path)`.
- Replace any matching write-side `.dump(...)` with `save_encodings(...)`.
- Remove the unsafe-serialization import once unused.
- For backward compatibility on first run, detect legacy binary files (starting with `\x80`) and migrate them by ignoring with a warning.

Helper sketch:
```python
import json
import logging
import os

import numpy as np


def save_encodings(path: str, encodings: dict) -> None:
    serializable = {
        name: [np.asarray(e).tolist() for e in enc_list]
        for name, enc_list in encodings.items()
    }
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(serializable, f)
    os.replace(tmp, path)


def load_encodings(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, 'rb') as f:
        head = f.read(2)
    if head[:1] == b'\x80':  # legacy binary marker
        logging.warning('legacy binary face encodings detected at %s; ignoring (delete and retrain)', path)
        return {}
    with open(path, 'r') as f:
        data = json.load(f)
    return {name: [np.asarray(e) for e in enc_list] for name, enc_list in data.items()}
```

- [ ] **Step 5: Replace unsafe deserialization in `tasks.py`**

`tasks.py:182` — use `json.load` / `json.dump` for the tasks queue. Tasks contain primitive types (camera_id, action name, kwargs of strings/ints). If any task value is non-JSON-serializable, document and convert.

```python
# OLD
with open(_TASKS_FILE, 'rb') as f:
    tasks = <unsafe>.load(f)

# NEW
with open(_TASKS_FILE, 'r') as f:
    tasks = json.load(f)
```

Make the corresponding write site use `json.dump`. Remove the legacy import.

- [ ] **Step 6: Replace unsafe deserialization in `extra/opencv_processor.py`**

Same pattern as Step 4 — switch persistence to JSON.

- [ ] **Step 7: Run tests to confirm pass**

Run: `python -m pytest tests/test_face_encoding_persistence.py tests/ -v`
Expected: New test passes; existing tests unchanged.

- [ ] **Step 8: Verify no unsafe loads remain**

Run: `grep -rn "\.load(" motioneye/ | grep -i pickle`
Expected: No matches.

- [ ] **Step 9: Commit**

```bash
git add motioneye/face_recognition_manager.py motioneye/tasks.py motioneye/extra/opencv_processor.py tests/test_face_encoding_persistence.py
git commit -m "security: replace unsafe deserialization with JSON (C3)

The previous binary-serialization format on attacker-influenced files
enabled RCE. Migrate face encodings, task queue, and opencv processor
state to JSON. Legacy binary files are detected and ignored with a warning."
```

---

### Task 1.4 (C4): Remove TLS certificate verification bypass

**Files:**
- Modify: `motioneye/utils/__init__.py:409-422`
- Modify: `motioneye/settings.py` (remove or repurpose `VALIDATE_CERTS`)
- Create: `tests/test_utils/test_tls.py`

- [ ] **Step 1: Locate the TLS bypass code**

Open `motioneye/utils/__init__.py` and read lines ~395-430. Identify the function/section that disables verification when `settings.VALIDATE_CERTS` is False.

- [ ] **Step 2: Write failing test**

Create `tests/test_utils/test_tls.py`:
```python
import inspect
import unittest

from motioneye import utils


class TlsVerificationTest(unittest.TestCase):
    def test_no_cert_none_in_module(self):
        src = inspect.getsource(utils)
        self.assertNotIn('CERT_NONE', src,
            "ssl.CERT_NONE bypass must be removed (C4)")

    def test_no_check_hostname_false(self):
        src = inspect.getsource(utils)
        compact = ''.join(src.split())
        self.assertNotIn('check_hostname=False', compact)
```

- [ ] **Step 3: Run test to confirm failure**

Run: `python -m pytest tests/test_utils/test_tls.py -v`
Expected: FAIL — `CERT_NONE` is in the source.

- [ ] **Step 4: Remove the bypass code path**

In `motioneye/utils/__init__.py`, remove the entire conditional that disables verification. The remaining code path must always use the system CA bundle (the default for `ssl.create_default_context()`).

If user-supplied CAs are needed, expose `settings.CA_BUNDLE_PATH` (optional file path) and pass it via `cafile=` to `ssl.create_default_context()`.

- [ ] **Step 5: Mark `VALIDATE_CERTS` as removed in settings**

In `motioneye/settings.py`, find `VALIDATE_CERTS` and either delete it or replace with a no-op deprecated stub:
```python
# Removed: TLS certificate verification is now always enforced.
# Use CA_BUNDLE_PATH to add custom CAs.
CA_BUNDLE_PATH = None
```

- [ ] **Step 6: Run tests to confirm pass**

Run: `python -m pytest tests/test_utils/ -v`
Expected: New test PASSES; existing tests unchanged.

- [ ] **Step 7: Commit**

```bash
git add motioneye/utils/__init__.py motioneye/settings.py tests/test_utils/test_tls.py
git commit -m "security: remove TLS certificate verification bypass (C4)

ssl.CERT_NONE / check_hostname=False allowed full MitM on outbound
HTTPS (webhooks, uploads, remote cameras). Always use system CA bundle;
add CA_BUNDLE_PATH setting for custom CAs."
```

---

## Phase 2: High-Priority Security & Process Hardening

### Task 2.1 (Q6): Fix `os.umask(0)` in daemonize

**Files:**
- Modify: `motioneye/server.py:75`
- Create: `tests/test_server_umask.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_server_umask.py`:
```python
import inspect
import unittest

from motioneye.server import Daemon


class DaemonUmaskTest(unittest.TestCase):
    def test_daemonize_does_not_use_world_writable_umask(self):
        src = inspect.getsource(Daemon.daemonize)
        self.assertNotIn('os.umask(0)', src,
            "umask(0) creates world-writable files (Q6)")
        self.assertIn('umask(0o027)', src.replace(' ', ''))
```

- [ ] **Step 2: Run test to confirm failure**

Run: `python -m pytest tests/test_server_umask.py -v`
Expected: FAIL — current code has `os.umask(0)`.

- [ ] **Step 3: Fix the umask**

In `motioneye/server.py:75`, change `os.umask(0)` to `os.umask(0o027)`.

- [ ] **Step 4: Run tests to confirm pass**

Run: `python -m pytest tests/test_server_umask.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add motioneye/server.py tests/test_server_umask.py
git commit -m "security: tighten daemon umask from 0 to 0o027 (Q6)

Previous umask(0) made all daemon-created files (config, logs,
recordings) world-readable and world-writable."
```

---

### Task 2.2 (Q9): Add Content-Security-Policy header

**Files:**
- Modify: `motioneye/handlers/base.py:175-186` (`finish` method)
- Create: `tests/test_handlers/test_security_headers.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_handlers/test_security_headers.py`:
```python
from motioneye.handlers.base import ManifestHandler
from tests.test_handlers import HandlerTestCase


class SecurityHeadersTest(HandlerTestCase):
    handler_cls = ManifestHandler

    def test_csp_header_set(self):
        response = self.fetch('/manifest.json')
        self.assertIn('Content-Security-Policy', response.headers)
        csp = response.headers['Content-Security-Policy']
        self.assertIn("default-src 'self'", csp)

    def test_hsts_only_on_https(self):
        # Plain HTTP should NOT send HSTS (header is ignored anyway and gives false security)
        response = self.fetch('/manifest.json')
        scheme = getattr(response.request, 'scheme', 'http')
        if scheme == 'http':
            self.assertNotIn('Strict-Transport-Security', response.headers)
```

- [ ] **Step 2: Run test to confirm failure**

Run: `python -m pytest tests/test_handlers/test_security_headers.py -v`
Expected: FAIL — CSP not set; HSTS sent on HTTP.

- [ ] **Step 3: Update `finish` in base.py**

In `motioneye/handlers/base.py:175-186`, modify the security headers block:
```python
def finish(self, chunk=None):
    if not self._finished:
        import motioneye

        self.set_header('Server', f'motionEye/{motioneye.VERSION}')
        self.set_header('X-Content-Type-Options', 'nosniff')
        self.set_header('X-Frame-Options', 'DENY')
        self.set_header('Referrer-Policy', 'no-referrer')
        self.set_header(
            'Content-Security-Policy',
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "media-src 'self' blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        # Only send HSTS on TLS connections
        if self.request.protocol == 'https':
            self.set_header(
                'Strict-Transport-Security',
                'max-age=31536000; includeSubDomains'
            )

        return super().finish(chunk=chunk)
    else:
        logging.debug('Already finished')
```

Removed the deprecated `X-XSS-Protection` header.

- [ ] **Step 4: Run tests to confirm pass**

Run: `python -m pytest tests/test_handlers/test_security_headers.py -v`
Expected: PASS.

- [ ] **Step 5: Manual smoke check**

Open the web UI, then in browser devtools open the Console. Confirm there are no CSP violations on the main page or camera pages. If any inline scripts trigger violations, capture them; either move them to a static file or add a nonce mechanism (note as follow-up; do not add `'unsafe-inline'` to script-src as a shortcut).

- [ ] **Step 6: Commit**

```bash
git add motioneye/handlers/base.py tests/test_handlers/test_security_headers.py
git commit -m "security: add CSP, gate HSTS to TLS, drop X-XSS-Protection (Q9)

- Strict CSP prevents inline script execution
- HSTS only on https (per RFC 6797 it's ignored over http anyway)
- X-XSS-Protection is deprecated/harmful in modern browsers
- Add Referrer-Policy: no-referrer"
```

---

### Task 2.3 (Q10): Persist cookie secret across restarts

**Files:**
- Modify: `motioneye/settings.py:167`
- Create: `motioneye/secrets_store.py`
- Create: `tests/test_secrets_store.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_secrets_store.py`:
```python
import os
import stat
import tempfile
import unittest

from motioneye import secrets_store


class SecretsStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, 'cookie.secret')

    def test_get_or_create_returns_64_hex_chars(self):
        secret = secrets_store.get_or_create_secret(self.path)
        self.assertEqual(len(secret), 64)
        int(secret, 16)  # raises if not hex

    def test_get_or_create_stable_across_calls(self):
        first = secrets_store.get_or_create_secret(self.path)
        second = secrets_store.get_or_create_secret(self.path)
        self.assertEqual(first, second)

    def test_secret_file_has_owner_only_perms(self):
        secrets_store.get_or_create_secret(self.path)
        mode = stat.S_IMODE(os.stat(self.path).st_mode)
        self.assertEqual(mode, 0o600)
```

- [ ] **Step 2: Run test to confirm failure**

Run: `python -m pytest tests/test_secrets_store.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `secrets_store`**

Create `motioneye/secrets_store.py`:
```python
"""Persistent secret storage with restrictive file permissions."""
import os
import secrets


def get_or_create_secret(path: str) -> str:
    """Return the hex secret stored at `path`, creating it if absent.

    The file is created with mode 0o600 (owner read/write only).
    """
    if os.path.exists(path):
        with open(path, 'r') as f:
            value = f.read().strip()
        if value:
            return value

    value = secrets.token_hex(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, value.encode('utf-8'))
    finally:
        os.close(fd)
    return value
```

- [ ] **Step 4: Run tests to confirm pass**

Run: `python -m pytest tests/test_secrets_store.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 5: Wire into settings.py**

In `motioneye/settings.py`, replace the line `COOKIE_SECRET = secrets.token_hex(32)` with:
```python
import os
from motioneye import secrets_store

_COOKIE_SECRET_FILE = os.path.join(CONF_PATH, 'cookie.secret')
COOKIE_SECRET = secrets_store.get_or_create_secret(_COOKIE_SECRET_FILE)
```

If `settings.py` is loaded before `CONF_PATH` is finalized, fall back to a path from an env var or defer the lookup. Verify by reading settings.py's existing structure.

- [ ] **Step 6: Run full suite**

Run: `python -m pytest tests/ -v`
Expected: No regressions.

- [ ] **Step 7: Manual smoke test**

Start the server, log in. Stop and restart. Verify the user remains logged in (or at minimum the cookie file exists with `0o600` perms): `ls -l <CONF_PATH>/cookie.secret`.

- [ ] **Step 8: Commit**

```bash
git add motioneye/settings.py motioneye/secrets_store.py tests/test_secrets_store.py
git commit -m "security: persist cookie secret across restarts (Q10)

Previously COOKIE_SECRET was regenerated on every boot, invalidating
all sessions. Now stored in <CONF_PATH>/cookie.secret with 0o600 perms."
```

---

### Task 2.4 (Q5): Re-enable XSRF protection

**Files:**
- Modify: `motioneye/handlers/base.py:113-127`
- Modify: `tests/test_handlers/test_login.py` (un-skip `test_full_password_change_workflow` once fixed)

- [ ] **Step 1: Write failing test**

Add to `tests/test_handlers/test_security_headers.py`:
```python
import inspect
import unittest
from motioneye.handlers.base import BaseHandler


class XsrfTest(unittest.TestCase):
    def test_check_xsrf_cookie_is_not_a_pass_stub(self):
        src = inspect.getsource(BaseHandler.check_xsrf_cookie)
        # Must not be just `pass` — extract last non-comment, non-docstring line
        lines = [l.strip() for l in src.splitlines() if l.strip() and not l.strip().startswith('#')]
        self.assertNotEqual(lines[-1], 'pass',
            "check_xsrf_cookie must not be a no-op (Q5)")
```

- [ ] **Step 2: Run test to confirm failure**

Run: `python -m pytest tests/test_handlers/test_security_headers.py::XsrfTest -v`
Expected: FAIL.

- [ ] **Step 3: Restore XSRF protection with a narrow exception**

Replace `check_xsrf_cookie` in `motioneye/handlers/base.py`:
```python
def check_xsrf_cookie(self):
    """Enforce XSRF cookie for state-changing requests.

    GET/HEAD/OPTIONS are XSRF-safe. POST/PUT/DELETE require a valid
    XSRF cookie. Signature-authenticated server-to-server requests
    (camera relay events) bypass via _signature presence.
    """
    if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
        return
    # Server-to-server signature auth (e.g. relay events from remote
    # cameras) authenticates with HMAC and does not have cookies.
    if self.get_argument('_signature', None):
        return
    super().check_xsrf_cookie()
```

- [ ] **Step 4: Run tests, fix any breakage**

Run: `python -m pytest tests/ -v`
Expected: Many handler tests may now require an `X-XSRFToken` header. Update them to include the header. The previously-skipped `test_full_password_change_workflow` may now be runnable — un-skip it and verify.

- [ ] **Step 5: Manual smoke test**

In a browser, exercise: login, change a camera setting, save config, view recordings, delete a recording, shutdown. All must succeed. Then attempt a cross-origin POST from `curl` without the XSRF cookie:
```bash
curl -X POST http://localhost:8765/config/main/set -d '{}' -H "Content-Type: application/json"
```
Expected: 403 (rejected).

- [ ] **Step 6: Commit**

```bash
git add motioneye/handlers/base.py tests/test_handlers/
git commit -m "security: restore XSRF protection for state-changing requests (Q5)

check_xsrf_cookie was a pass stub. Now enforces XSRF cookie for
POST/PUT/DELETE. Signature-authenticated server-to-server requests
(_signature param present) bypass the check, since they use HMAC."
```

---

### Task 2.5 (Q11): Use credentials file for SMB mount instead of CLI args

**Files:**
- Modify: `motioneye/controls/smbctl.py:218-239`
- Create: `tests/test_controls/__init__.py`, `tests/test_controls/test_smbctl.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_controls/__init__.py` (empty) and `tests/test_controls/test_smbctl.py`:
```python
import inspect
import unittest

from motioneye.controls import smbctl


class SmbctlSecurityTest(unittest.TestCase):
    def test_password_not_passed_via_cli(self):
        src = inspect.getsource(smbctl)
        compact = ''.join(src.split())
        self.assertNotIn(",password=", compact,
            "SMB password must not appear in mount.cifs options string (Q11)")
        self.assertIn('credentials=', src,
            "Use credentials file for mount.cifs")
```

- [ ] **Step 2: Run test to confirm failure**

Run: `python -m pytest tests/test_controls/test_smbctl.py -v`
Expected: FAIL.

- [ ] **Step 3: Refactor SMB mount to use credentials file**

In `motioneye/controls/smbctl.py`, locate the `mount.cifs` invocation. Replace inline `username=...,password=...` options with a credentials file:
```python
import os
import tempfile

def _write_credentials_file(username: str, password: str, domain: str = '') -> str:
    fd, path = tempfile.mkstemp(prefix='smbcred-', suffix='.cred')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(f'username={username}\n')
            f.write(f'password={password}\n')
            if domain:
                f.write(f'domain={domain}\n')
        os.chmod(path, 0o600)
        return path
    except Exception:
        os.unlink(path)
        raise

# Usage in the mount call:
cred_path = _write_credentials_file(username, password, domain)
try:
    options = f'credentials={cred_path}'  # plus other non-secret options
    subprocess.run(['mount.cifs', share, mountpoint, '-o', options], check=True)
finally:
    os.unlink(cred_path)
```

- [ ] **Step 4: Run tests to confirm pass**

Run: `python -m pytest tests/test_controls/test_smbctl.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add motioneye/controls/smbctl.py tests/test_controls/
git commit -m "security: use credentials file for SMB mount (Q11)

Passing password=... in the mount.cifs -o options string exposed
the password to any local user via /proc/<pid>/cmdline. Use a
0o600 credentials file instead, deleted after mount completes."
```

---

## Phase 3: Code Quality & Architecture

### Task 3.1 (Q1): Eliminate dead `make_app()` duplication

**Files:**
- Modify: `motioneye/server.py:545-553`
- Create: `tests/test_server_app.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_server_app.py`:
```python
import inspect
import unittest

from motioneye import server


class ServerAppDuplicationTest(unittest.TestCase):
    def test_run_does_not_construct_application_inline(self):
        src = inspect.getsource(server.run)
        self.assertIn('make_app(', src)
        self.assertNotIn('Application(\n        handler_mapping', src)
```

- [ ] **Step 2: Run test to confirm failure**

Run: `python -m pytest tests/test_server_app.py -v`
Expected: FAIL.

- [ ] **Step 3: Replace inline Application with `make_app()`**

In `motioneye/server.py:545-553`, replace the inline `Application(...)` block with:
```python
application = make_app(debug=False)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_server_app.py tests/ -v`
Expected: PASS, no regressions.

- [ ] **Step 5: Commit**

```bash
git add motioneye/server.py tests/test_server_app.py
git commit -m "refactor: use make_app() in run() instead of duplicating (Q1)

Previously make_app() was dead code while run() constructed an
identical Application inline."
```

---

### Task 3.2 (Q2): Remove per-request `gc.collect()` from BaseHandler

**Files:**
- Modify: `motioneye/handlers/base.py:33-65`
- Add to: `tests/test_handlers/test_base.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_handlers/test_base.py`:
```python
def test_cleanup_does_not_call_gc_collect(self):
    import inspect
    from motioneye.handlers.base import BaseHandler
    src = inspect.getsource(BaseHandler._cleanup)
    self.assertNotIn('gc.collect', src,
        "Per-request gc.collect() stalls the event loop (Q2)")
```

- [ ] **Step 2: Run test to confirm failure**

Run: `python -m pytest tests/test_handlers/test_base.py -v -k gc`
Expected: FAIL.

- [ ] **Step 3: Strip the gc.collect call from `_cleanup`**

In `motioneye/handlers/base.py`, simplify `_cleanup` to only release the `_image_data` reference. Remove the `_active_handlers > 50` branch and the `gc.collect()` call. Remove `import gc` if no longer used.

```python
def _cleanup(self):
    """Drop large per-request buffers to help GC."""
    if getattr(self, '_cleanup_done', False):
        return
    self._cleanup_done = True
    if hasattr(self, '_image_data'):
        self._image_data = None
```

- [ ] **Step 4: Run tests to confirm pass**

Run: `python -m pytest tests/test_handlers/test_base.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add motioneye/handlers/base.py
git commit -m "perf: remove per-request gc.collect from BaseHandler (Q2)

gc.collect() on every request with >50 active handlers stalls the
Tornado event loop. Python's generational GC handles this automatically;
no manual triggers needed in the request hot path."
```

---

### Task 3.3 (Q3): Move per-request imports in base.py to module level

**Files:**
- Modify: `motioneye/handlers/base.py`

- [ ] **Step 1: Identify per-request imports**

Run: `grep -n "import motioneye" motioneye/handlers/base.py`
Expected: Two occurrences inside `finish()` and `render()`.

- [ ] **Step 2: Verify no circular import problem**

Read `motioneye/__init__.py`. Confirm it does not import `handlers.base` (which would make the module-level import circular).

- [ ] **Step 3: Move import to module top**

Add `import motioneye` at the top of `motioneye/handlers/base.py`. Remove the in-function imports.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/ -v`
Expected: No regressions. If circular import surfaces, revert and use `from motioneye import VERSION` at top instead.

- [ ] **Step 5: Commit**

```bash
git add motioneye/handlers/base.py
git commit -m "refactor: hoist per-request \`import motioneye\` to module level (Q3)"
```

---

### Task 3.4 (Q4): Clean up `configure_high_performance_ioloop`

**Files:**
- Modify: `motioneye/server.py:457-481`

- [ ] **Step 1: Read the function**

Open `motioneye/server.py:457-481`. Note: `import logging` is shadowed inside; `tornado.platform.asyncio.AsyncIOMainLoop().install()` is deprecated in Tornado 6+.

- [ ] **Step 2: Refactor**

Replace the function body:
```python
def configure_high_performance_ioloop():
    """Configure Tornado for maximum performance."""
    import asyncio
    import resource

    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logging.info('Using uvloop for high-performance event loop')
    except ImportError:
        logging.info('uvloop not available, using default asyncio')

    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        target = min(4096, hard)
        resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
        logging.info(f'File descriptor limit set to {target}')
    except (OSError, ValueError) as e:
        logging.warning(f'Could not increase file descriptor limit: {e}')
```

Removed:
- Shadowing `import logging` (already imported at top of file)
- Deprecated `AsyncIOMainLoop().install()` call (no-op or harmful on Tornado 6.x; uvloop is set via the asyncio policy, which Tornado 6 picks up automatically)

- [ ] **Step 3: Run tests and start server manually**

Run: `python -m pytest tests/ -v` then `python -m motioneye.meyectl startserver` and confirm the log line "Using uvloop..." or "uvloop not available..." appears, and the server accepts requests on the configured port.

- [ ] **Step 4: Commit**

```bash
git add motioneye/server.py
git commit -m "cleanup: simplify configure_high_performance_ioloop (Q4)

Remove shadowed \`import logging\` and deprecated AsyncIOMainLoop.install()
call. uvloop is auto-picked-up by Tornado 6 via asyncio policy."
```

---

## Phase 4: Cleanup & Tech Debt

### Task 4.1 (J1): Remove duplicate codec functions in `motionctl.py`

**Files:**
- Modify: `motioneye/motionctl.py:392-507`
- Create: `tests/test_motionctl_codec.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_motionctl_codec.py`:
```python
import inspect
import unittest

from motioneye import motionctl


class MotionctlDuplicationTest(unittest.TestCase):
    def test_no_duplicate_codec_function_names(self):
        src = inspect.getsource(motionctl)
        names = [
            'has_h264_nvenc_support', 'has_h264_nvmpi_support',
            'has_hevc_nvmpi_support', 'has_hevc_nvenc_support',
            'has_h264_qsv_support', 'has_hevc_qsv_support',
        ]
        for n in names:
            occurrences = src.count(f'def {n}(')
            self.assertEqual(occurrences, 1,
                f'{n} is defined {occurrences} times (J1)')
```

- [ ] **Step 2: Run test to confirm failure**

Run: `python -m pytest tests/test_motionctl_codec.py -v`
Expected: FAIL — each function defined twice.

- [ ] **Step 3: Delete the duplicate definitions**

In `motioneye/motionctl.py`, delete lines ~452-507 (the second definitions). Keep the first set at lines ~392-447.

- [ ] **Step 4: Run tests to confirm pass**

Run: `python -m pytest tests/test_motionctl_codec.py tests/ -v`
Expected: PASS, no regressions.

- [ ] **Step 5: Commit**

```bash
git add motioneye/motionctl.py tests/test_motionctl_codec.py
git commit -m "fix: remove 6 duplicated codec-support functions (J1)

Six has_*_support functions were defined twice with identical bodies;
the second set silently shadowed the first."
```

---

### Task 4.2 (J2): Delete redundant CI workflows

**Files:**
- Delete: `.github/workflows/ci-linux.yml`
- Delete: `.github/workflows/ci-macos.yml`

- [ ] **Step 1: Verify ci.yml covers both platforms**

Run: `grep -E "(ubuntu|macos)" .github/workflows/ci.yml`
Expected: Both `ubuntu-latest` and `macos-latest` appear in ci.yml's matrix.

- [ ] **Step 2: Delete the redundant workflows**

```bash
git rm .github/workflows/ci-linux.yml .github/workflows/ci-macos.yml
```

- [ ] **Step 3: Push branch and verify CI**

After committing, push the branch and verify in GitHub Actions that `ci.yml` still runs the full matrix and `ci-linux`/`ci-macos` no longer appear.

- [ ] **Step 4: Commit**

```bash
git commit -m "ci: remove redundant ci-linux.yml and ci-macos.yml (J2)

ci.yml already runs the full {ubuntu,macos} x {3.11,3.13} matrix."
```

---

### Task 4.3 (J3): Remove unused imports

**Files:**
- Modify: `motioneye/motionctl.py:24` — remove `from shlex import quote`
- Modify: `motioneye/monitor.py:20` — remove `import urllib.error`
- Modify: `motioneye/webhook.py:19` — remove `import urllib.error`
- Modify: `motioneye/utils/__init__.py:27` — remove `import urllib.error`
- Modify: `test_motioneye_lite.py` — remove `import tempfile`
- Modify: `test_integration.py` — remove `from unittest.mock import patch`
- Modify: `tests/test_handlers/test_login.py` — remove `from urllib.parse import urlencode`

- [ ] **Step 1: Verify each unused import**

For each import, confirm it is unused with grep. Example for `shlex.quote`:
```bash
grep -n "quote(" motioneye/motionctl.py
```
Expected: No usages, or only inside docstring/comment.

If any *is* used, do not remove that one — note in the commit message.

- [ ] **Step 2: Remove the imports**

Edit each file accordingly.

- [ ] **Step 3: Run tests and lint**

Run: `python -m pytest tests/ -v && python -m flake8 motioneye/ tests/ 2>&1 | head -40`
Expected: No regressions; flake8 should now have fewer F401 warnings.

- [ ] **Step 4: Commit**

```bash
git add motioneye/motionctl.py motioneye/monitor.py motioneye/webhook.py motioneye/utils/__init__.py test_motioneye_lite.py test_integration.py tests/test_handlers/test_login.py
git commit -m "cleanup: remove 7 unused imports (J3)"
```

---

### Task 4.4 (J4): Address RTMP stub and JS UI TODOs

**Files:**
- Modify: `motioneye/utils/rtmp.py` — implement TCP connectivity check OR document
- Modify: `motioneye/static/js/ui.js:261,280` — implement OR remove dead handlers

- [ ] **Step 1: Decide: implement or document?**

Read `motioneye/utils/rtmp.py:check_rtmp_url` and inspect the JS UI handlers around `ui.js:261` and `ui.js:280`. If the project does not currently support RTMP streams in production, document the stubs and move on. If it does, implement them.

For the simpler path (document), add a docstring:
```python
def check_rtmp_url(*args, **kwargs):
    """Return a stub camera response.

    NOTE: This function intentionally does not validate RTMP reachability.
    See docs/MOTIONEYE_LITE.md for the supported camera-discovery mechanisms;
    RTMP discovery is deferred until a real implementation is needed.
    """
```

For `ui.js:261` and `ui.js:280`, if the snap-mode-1 left/right arrow handlers are truly unused, delete the empty stubs entirely. If a handler signature is needed for the framework to bind to, log a no-op and remove the TODO.

- [ ] **Step 2: Verify nothing broke**

Run: `python -m pytest tests/ -v`. Smoke test the web UI keyboard navigation.

- [ ] **Step 3: Commit**

```bash
git add motioneye/utils/rtmp.py motioneye/static/js/ui.js
git commit -m "cleanup: document RTMP stub, remove empty JS arrow handlers (J4)"
```

---

### Task 4.5 (J5): Move or remove orphan test files

**Files:**
- Move: `test_integration.py` → `tests/test_integration.py` (or delete)
- Move: `test_motioneye_lite.py` → `tests/test_motioneye_lite.py` (or keep as-is and update CI)

- [ ] **Step 1: Decide per-file**

For `test_integration.py`: read it. If it provides value, move it under `tests/` so `pytest tests/` picks it up. If it's stale, delete it.

For `test_motioneye_lite.py`: it is already invoked separately by CI. Move it under `tests/` and update the CI workflow that runs it to point to the new path.

- [ ] **Step 2: Move the files**

```bash
git mv test_integration.py tests/test_integration.py
git mv test_motioneye_lite.py tests/test_motioneye_lite.py
```

(Or `git rm` if deleting.)

- [ ] **Step 3: Update CI references**

Run: `grep -rn "test_motioneye_lite\|test_integration" .github/`
Update any matches to point to the new path.

- [ ] **Step 4: Run full suite**

Run: `python -m pytest tests/ -v`
Expected: Both relocated tests now run. Fix any import-path issues that surface.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "test: relocate orphan test files into tests/ (J5)

Both files lived at the project root and were invisible to pytest tests/.
Now consolidated under tests/ and CI workflows updated."
```

---

### Task 4.6 (J6): Replace `DEV_NULL` module-global with `subprocess.DEVNULL`

**Files:**
- Modify: `motioneye/utils/__init__.py:44`
- Modify: All callers of `utils.DEV_NULL`

- [ ] **Step 1: Find all callers**

Run: `grep -rn "DEV_NULL" motioneye/`
Expected: List of references.

- [ ] **Step 2: Replace each call site**

For each caller, replace `utils.DEV_NULL` (or `from .utils import DEV_NULL`) with `subprocess.DEVNULL` (importing `subprocess` if not already imported).

- [ ] **Step 3: Remove the global**

Delete the `DEV_NULL = open('/dev/null', 'w')` line from `motioneye/utils/__init__.py`.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/ -v`
Expected: No regressions.

- [ ] **Step 5: Commit**

```bash
git add motioneye/
git commit -m "cleanup: replace DEV_NULL global with subprocess.DEVNULL (J6)"
```

---

## Phase 5: Final Verification

### Task 5.1: Full regression sweep

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest -v 2>&1 | tail -40`
Expected: All tests pass (or skipped tests match the baseline established in Task 0.1.2).

- [ ] **Step 2: Run lint**

Run: `python -m flake8 motioneye/ tests/`
Expected: No new errors compared to the baseline.

- [ ] **Step 3: Run a manual smoke test of the full app**

1. Start the server.
2. Log in as admin (verify password upgrade to bcrypt happens transparently).
3. Add a camera.
4. View a live stream.
5. Trigger a recording.
6. Browse recordings, delete one.
7. Open Preferences, change a setting.
8. Log out, log back in.
9. Restart the server, verify session is preserved (Q10).
10. Inspect the browser devtools Network tab on a few requests — confirm CSP, no HSTS over HTTP, no `X-XSS-Protection`.
11. Curl a state-changing endpoint without XSRF token — expect 403.

- [ ] **Step 4: Push branch and open PR**

```bash
git push -u origin audit-fixes-2026-05
gh pr create --title "Comprehensive security and quality audit fixes" --body "$(cat <<'EOF'
## Summary

Implements all 21 findings from the 2026-05-03 comprehensive audit.

### Critical security
- C1: SHA-1 → bcrypt password hashing (with backward-compatible verify)
- C2: hmac.compare_digest for signature comparison
- C3: Unsafe deserialization → JSON for persisted state
- C4: Removed TLS certificate verification bypass

### High-priority hardening
- Q5: Restored XSRF protection
- Q6: Tightened daemon umask 0 → 0o027
- Q7: Hash normal user password (was plaintext)
- Q8: Removed pass-the-hash in basic auth
- Q9: Added Content-Security-Policy, gated HSTS to TLS
- Q10: Persisted cookie secret across restarts
- Q11: SMB credentials moved to file (not CLI args)

### Code quality
- Q1: Removed dead make_app() duplication
- Q2: Removed per-request gc.collect()
- Q3: Hoisted per-request imports
- Q4: Cleaned up ioloop config

### Cleanup
- J1: Removed 6 duplicate codec functions
- J2: Deleted redundant CI workflows
- J3: Removed 7 unused imports
- J4: Documented RTMP stub, removed dead JS handlers
- J5: Relocated orphan test files
- J6: Replaced DEV_NULL with subprocess.DEVNULL

## Test plan
- [x] \`pytest tests/\` — all green
- [x] Manual smoke test (login, cameras, recording, restart, CSP, XSRF)
- [x] Verify password upgrade migration on first login
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** All 4 critical, 7 high-priority security/quality, 4 architecture, and 6 cleanup findings have a dedicated task. Total: 21 findings + Phase 0 setup + Phase 5 verification.
- **Type consistency:** `passwords.hash_password` / `verify_password` / `is_legacy_hash` — names used consistently across Tasks 1.1 and downstream references. `secrets_store.get_or_create_secret` — name consistent in Task 2.3.
- **No placeholders:** Each task includes actual code blocks for both tests and implementations. Diff blocks show before/after where ambiguous.
- **Backward compatibility:** Task 1.1 preserves SHA-1 verification so existing deployments continue to work; passwords transparently upgrade on next change. Task 1.3 detects legacy binary files and warn-logs rather than crashing.
