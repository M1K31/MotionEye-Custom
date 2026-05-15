# Contributing to MotionEye Custom

Thanks for your interest in contributing! This document covers the
PR process and code style. For local setup, testing, debugging, and
architecture see [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

---

## Quick start

```bash
git clone https://github.com/M1K31/MotionEye-Custom.git
cd MotionEye-Custom
make dev-install      # bootstraps motioneye_env/ and installs everything
make test             # 61 passing as of audit-fixes-2026-05
```

Already-cloned tree? `make dev-install` is idempotent.

---

## PR workflow

1. **Branch from `main`** (or the relevant feature branch):

   ```bash
   git checkout -b feature/short-descriptive-name
   ```

2. **Make focused changes.** One logical change per PR. Big efforts
   get a plan first — see [`docs/superpowers/plans/`](docs/superpowers/plans/)
   for the template.

3. **Add or update tests** for any behaviour change. Test-driven
   development is the project default; see [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)
   for the test layout.

4. **Run the local checks** before pushing:

   ```bash
   make test
   make lint     # flake8
   make format   # black
   ```

5. **Commit with conventional-commit prefixes.** Examples:

   ```
   feat(camera): add per-platform Add Camera gating
   fix(server): use writable RUN_PATH on macOS
   security(auth): replace SHA-1 password hashing with bcrypt
   docs(readme): refresh after audit
   test(handlers): add CSP nonce regression test
   build(macos): patch upstream Motion ulong portability bug
   ```

6. **Push and open a PR** against `main`. Reference any related
   issues. Include screenshots for UI changes.

---

## Code style

- **Python**: PEP 8, max line length 88 (Black's default). Run
  `make format` to auto-fix. `make lint` runs `flake8`.
- **JavaScript**: 4-space indent, matches existing `motioneye/static/js/`
  files. No new inline `<script>` tags without a `nonce`; no
  `href="javascript:..."` URLs (CSP blocks them — use
  `data-action` + the delegated click dispatcher in `main.js`).
- **HTML templates** in `motioneye/templates/`: no inline event
  handlers (`onclick="..."`). Bind from JS.

---

## Reporting issues

### Bug report essentials

- MotionEye version (`/version` endpoint or `pip show motioneye`)
- Host OS + Python version
- Steps to reproduce
- Expected vs actual behaviour
- Relevant log excerpts (server log, browser DevTools console)
- Camera type if relevant

### Feature requests

Describe the use case first, then the proposed mechanism. Smaller,
well-scoped requests merge faster than "rewrite X".

---

## Where things live

```
motioneye/                # main package
├── handlers/             # Tornado request handlers
├── controls/             # platform-specific camera/disk/SMB control
├── static/, templates/   # web UI (jQuery + Jinja2)
├── utils/                # cross-cutting helpers
└── platform_caps.py      # per-host camera capability detection

tests/                    # pytest suites mirror motioneye/
docs/                     # human-facing docs (this file points there)
docker/                   # Dockerfile + compose
build/                    # platform build scripts
```

Deeper architecture notes: [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

---

## License

By contributing you agree your contributions will be licensed under
[GPL-3.0](LICENSE).
