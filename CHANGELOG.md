# Changelog

All notable changes are documented in this file. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/); the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security (audit 2026-05-03 / branch `audit-fixes-2026-05`)

- **C1+Q7+Q8 — bcrypt password storage**: replaced SHA-1 admin/normal
  password hashing with bcrypt. Dual-hash storage preserves the JS
  client's HMAC signature contract: `@*_password` holds the bcrypt
  hash (used for login + HTTP Basic Auth), `@*_password_sig_key` holds
  `sha1(password)` (used as the HMAC key for signed API requests).
  Legacy SHA-1 hashes verify transparently and upgrade on next save.
  Normal user password is no longer stored plaintext. Basic auth no
  longer accepts the stored hash as a valid password (pass-the-hash
  hole closed).
- **C2 — timing-safe signature comparison**: `BaseHandler.get_current_user`
  now uses `hmac.compare_digest` instead of `==` to compare signatures.
- **C3 — JSON persistence**: replaced unsafe binary serialization in
  `face_recognition_manager.py`, `tasks.py`, and `opencv_processor.py`
  with JSON. Legacy binary files are detected by header and ignored
  with a warning.
- **C4 — TLS verification always enforced**: removed `ssl.CERT_NONE`
  bypass for outbound HTTPS (webhooks, uploads, remote cameras, MJPEG
  streams). Footgun `VALIDATE_CERTS = False` setting deleted; added
  `CA_BUNDLE_PATH` for custom CAs.
- **Q5 — XSRF protection restored**: `check_xsrf_cookie` no longer a
  pass-stub. Enforces token for state-changing requests; signature-
  authenticated server-to-server requests (`_signature` param) and the
  session-bootstrap `/login/` endpoint bypass.
- **Q6 — daemon umask hardened**: `os.umask(0)` → `0o027` so config,
  logs, and recordings are no longer world-writable.
- **Q9 — Content-Security-Policy**: strict CSP with per-request
  nonces for inline scripts. HSTS gated to HTTPS only. Deprecated
  `X-XSS-Protection` header removed. `X-Frame-Options: SAMEORIGIN`
  + `frame-ancestors 'self'` allows the same-origin login modal
  while blocking cross-origin clickjacking.
- **Q10 — persistent cookie secret**: `COOKIE_SECRET` stored at
  `$CONF_PATH/cookie.secret` (mode `0o600`) so sessions survive
  restarts.
- **Q11 — SMB credentials via creds file**: `mount.cifs` no longer
  receives the password on its CLI; written to a `0o600` tmp file
  referenced via `credentials=<path>` (keeps password out of
  `/proc/<pid>/cmdline`).
- Replaced `href="javascript:..."` links in `main.html` and `main.js`
  with `data-action` + delegated click dispatcher (CSP correctly
  blocks `javascript:` URL navigation).
- Removed 6 duplicate `has_*_support` codec functions in `motionctl.py`.

### Added

- **Cross-platform camera discovery (`motioneye.platform_caps`)**:
  per-backend capability detection drives the Add Camera dropdown.
  User-friendly labels with technical backend in parentheses, e.g.
  "Built-in or USB Camera (AVFoundation)" on macOS, "USB Webcam (V4L2)"
  on Linux, "Raspberry Pi Camera Module (MMAL)" on Pi. Options are
  hidden on hosts where the backend cannot work.
- macOS: `~/.local/bin/motion` installable via `build/build_motion_macos.sh`
  without sudo. Build script auto-applies a `ulong → unsigned long`
  portability patch needed for clang.
- `MOTIONEYE_RUN_PATH` and `MOTIONEYE_LOG_PATH` environment variables
  (parity with the existing `MOTIONEYE_CONF_PATH` / `MOTIONEYE_MEDIA_PATH`).
- New test suites covering passwords, secrets store, daemon umask,
  platform caps, JSON persistence, signature comparison, security
  headers, main caps rendering, SMB controls, and TLS verification.
  Test count: 11 baseline → 61 passing.

### Changed

- `Makefile dev-install` now bootstraps `motioneye_env/` on a fresh
  clone (was assumed pre-existing).
- `RUN_PATH` and `LOG_PATH` detection requires writability (not just
  existence) so the server starts non-root on macOS where
  `/var/run` exists but is root-only.
- `tasks.py` multiprocessing pool initialiser hoisted to module level
  so `spawn` (Python 3.8+ default on macOS) can serialize it.
- `build/build_motion_macos.sh`: adds `autoconf`/`libtool` to brew
  deps, shallow clone, parallel make, applies macOS portability
  patch, exports `PKG_CONFIG_PATH` from `brew --prefix`.
- Removed `DEV_NULL` module global in favour of `subprocess.DEVNULL`.

### Fixed

- `Daemon.daemonize` `umask(0)` made all daemon-created files world-
  writable.
- `BaseHandler` per-request `gc.collect()` stalled the Tornado event
  loop on bursty workloads.
- Per-request `import motioneye` hoisted to module level; cleaned up
  shadowed imports in `configure_high_performance_ioloop`.
- `.gitignore` typo `*~motioneye_env/` (which matched only files
  ending in `~motioneye_env/`) → proper `motioneye_env/` entry.
- Redundant CI workflows (`ci-linux.yml`, `ci-macos.yml`) removed;
  `ci.yml` already runs the full {ubuntu,macos} × {3.11,3.13} matrix.
- 7 unused imports across `motionctl`, `monitor`, `webhook`,
  `utils/__init__`, and test files.
- 27 lines of unreachable dead code in `build/install_macos.sh`.

### Removed

- `VALIDATE_CERTS` setting (replaced by `CA_BUNDLE_PATH`).
- `NEW_FEATURES.md` (content consolidated into `docs/USAGE.md`,
  `docs/MOTIONEYE_LITE.md`, and this changelog).
- `DEVELOPMENT.md` at repository root (moved to `docs/DEVELOPMENT.md`).

---

## Roadmap / Known Follow-ups

These are intentionally deferred from the audit and tracked here so
they're not forgotten.

- **Full SHA-1 retirement from signed-API contract.** Today the JS
  client signs every authenticated API request with `sha1(password)`
  as the HMAC key; the server stores that derived value as
  `@*_password_sig_key` alongside the bcrypt password hash. Fully
  retiring SHA-1 requires rewriting the client signature flow (in
  `motioneye/static/js/main.js`) — likely to a per-session bearer
  token with a server-stored secret. Captured in
  `docs/superpowers/plans/2026-05-03-comprehensive-audit-fixes.md`.
- **CSP `report-uri` endpoint + report-only staging toggle.** Plan at
  `docs/superpowers/plans/2026-05-11-csp-production-hardening.md`.
- **Playwright-based end-to-end CSP regression test in CI.** Plan at
  the same path.
- **AVFoundation device permission UX on macOS.** Camera enumeration
  via `ffmpeg -f avfoundation -list_devices true` requires macOS
  Camera permission (TCC) which CLI processes typically don't have.
  Needs a wrapper app or `tccutil` flow.
- **macOS Lite installer:** `docs/MOTIONEYE_LITE.md` previously
  referenced a `motioneye-lite` command and `test-system-readiness.sh`
  script that don't exist in the repo. Either build them or rewrite
  the doc to reflect the actual scripts (`build/build_motion_lite_macos.sh`,
  `build/install_macos.sh`).
<!-- 2026-05-16: the "transient 403 during first-boot password setup"
     entry that was here previously was a misdiagnosis. It only
     fires when the browser has stale meye_username /
     meye_password_hash cookies in the profile (e.g. from prior
     testing on the same hostname or a different MotionEye
     instance). The 403 is the correct semantic response for an
     invalid signature and the existing ajax() error handler
     recovers by opening the login dialog. Fresh clients (incognito,
     cookies cleared) see zero 403s — verified with a
     throwaway-container Chrome DevTools MCP repro on 2026-05-16.
     Not a bug. -->


---

## [0.43.1b4] - 2024

Initial fork from the upstream
[motioneye-project/motioneye](https://github.com/motioneye-project/motioneye).
Inherits core motion detection, web UI, multi-camera support, email
and webhook notifications, and the Motion daemon integration. See
upstream changelog for prior history.

---

## Upgrade Notes

### Docker users

```bash
docker pull im1k31s/motioneye-custom:latest
docker compose down && docker compose pull && docker compose up -d
```

### Native installs

Existing SHA-1-hashed admin passwords keep working — the
backward-compatible verifier upgrades the stored hash to bcrypt on
the next password change. To force the upgrade without changing the
password, save any other config setting through the web UI.

### Removed settings

- `VALIDATE_CERTS = False` no longer disables TLS verification. Set
  `CA_BUNDLE_PATH = "/path/to/ca.pem"` if you need a custom CA bundle
  (e.g., self-signed cameras).

---

## Support

- **Documentation:** [`docs/`](docs/)
- **Issues:** [GitHub Issues](https://github.com/M1K31/MotionEye-Custom/issues)
- **Discussions:** [GitHub Discussions](https://github.com/M1K31/MotionEye-Custom/discussions)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md)
