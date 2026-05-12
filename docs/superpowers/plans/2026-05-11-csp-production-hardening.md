# CSP Production Hardening Plan

> **Sub-skill:** Use superpowers:subagent-driven-development or executing-plans to implement task-by-task.

**Goal:** Drive the Content-Security-Policy adopted in Q9 to a fully production-ready state by closing every browser-surfaced violation found during manual smoke testing, then adding a CI safety net so regressions surface before deploy.

**Architecture:** Three browser violations were caught during smoke testing of `audit-fixes-2026-05`. Two are already fixed inline (commit `482864fd`) — this plan covers (a) verifying the in-flight fixes hold in a real browser, (b) hunting and fixing the third reported "Add Camera" violation, and (c) building permanent guards (lint rule for inline handlers, CSP violation reporting, browser-driven CI test).

**Tech Stack:** Python 3.9+, Tornado 6.x, pytest, jQuery/JS UI, Playwright (proposed for end-to-end CSP test).

---

## Phase 1: Verify In-Flight Fixes (smoke test)

### Task 1.1: Manual browser smoke against the running test server

**Files:** none — manual

- [ ] **Step 1: Restart the dev server**
  ```
  lsof -ti:8765 | xargs kill 2>/dev/null
  mkdir -p /tmp/motioneye-test/{run,log,media}
  MOTIONEYE_CONF_PATH=/tmp/motioneye-test/conf \
    MOTIONEYE_RUN_PATH=/tmp/motioneye-test/run \
    MOTIONEYE_LOG_PATH=/tmp/motioneye-test/log \
    MOTIONEYE_MEDIA_PATH=/tmp/motioneye-test/media \
    motioneye_env/bin/python -m motioneye.meyectl startserver -d &
  ```

- [ ] **Step 2: Hard-reload the browser** (Cmd-Shift-R / Ctrl-F5) at http://localhost:8765/
  The previous CSP errors were partly cached; the cached headers must be evicted.

- [ ] **Step 3: Confirm DevTools console is clean at the landing page**
  Expected: no CSP violations, no `ReferenceError: Can't find variable: frame`.
  The login modal iframe should now render (`frame-ancestors 'self'` allows same-origin).

- [ ] **Step 4: Log in** with `admin` / `admin` and complete the forced password change.
  Expected: bcrypt verification succeeds, `@admin_password_sig_key` rewrites.

- [ ] **Step 5: Click the Add Camera button.**
  Expected: dialog opens. If the same CSP violation reappears, capture:
  - exact error text and source URL/line from DevTools Console
  - `document.querySelectorAll('script')` snapshot to identify any `<script>` without a nonce that the dialog injected
  - the Network tab response that introduced it
  Record findings in `docs/superpowers/notes/csp-add-camera-investigation.md`.

- [ ] **Step 6: Click User Profile.**
  Expected: opens the change-password panel (not a full page navigation). If it still navigates to `/login/`, that is a *behavioural* bug to address separately, not a CSP regression.

---

## Phase 2: Resolve any remaining "Add Camera" CSP violations

> **Run Phase 2 only if Phase 1 Step 5 still shows a violation.**

### Task 2.1: Identify the injected script source

**Files:** `motioneye/static/js/main.js`, possibly `motioneye/static/js/ui.js`

- [ ] **Step 1: Search for any client-side HTML injection that could contain `<script>`.**

  Run: `grep -nE "\.html\(|\.append\(|innerHTML" motioneye/static/js/*.js | grep -iE "<script|gettext"`
  Expected output: enumerate every site where a translation or remote response is dropped into the DOM.

- [ ] **Step 2: Inspect translation JSONs for embedded HTML/script.**

  Run: `python -c "import json,glob; [print(p) for p in glob.glob('motioneye/static/js/motioneye.*.json') if '<script' in open(p).read() or 'javascript:' in open(p).read()]"`
  Expected: empty. If non-empty, those translation files must be sanitised or the data path must be plain-text via `.text(...)`.

- [ ] **Step 3: Switch unsafe HTML injection to safe text/element APIs.**

  Wherever a string contains user-or-translation-controlled data and goes into `.html(...)`, switch to `.text(...)`, `.append($('<el>').text(...))`, or use a template element. Capture before/after diff in the PR description.

- [ ] **Step 4: Re-test in browser, confirm violation is gone.**

### Task 2.2: Add CSP violation reporting endpoint

**Files:** Create `motioneye/handlers/csp_report.py`, modify `motioneye/server.py` (URL mapping), modify `motioneye/handlers/base.py` (CSP `report-uri`)

- [ ] **Step 1: Write the failing test.**

  Create `tests/test_handlers/test_csp_report.py`:
  ```python
  import json
  from tests.test_handlers import HandlerTestCase
  from motioneye.handlers.csp_report import CspReportHandler


  class CspReportTest(HandlerTestCase):
      handler_cls = CspReportHandler

      def test_post_logs_violation_and_returns_204(self):
          report = {
              'csp-report': {
                  'document-uri': 'http://localhost/x',
                  'violated-directive': 'script-src',
                  'blocked-uri': 'inline',
              }
          }
          response = self.fetch(
              '/csp-report',
              method='POST',
              headers={'Content-Type': 'application/csp-report'},
              body=json.dumps(report),
          )
          self.assertEqual(204, response.code)
  ```

- [ ] **Step 2: Run, verify failure.**

- [ ] **Step 3: Implement the handler.**

  Create `motioneye/handlers/csp_report.py`:
  ```python
  import json
  import logging

  from motioneye.handlers.base import BaseHandler


  class CspReportHandler(BaseHandler):
      # CSP report POSTs are user-agent-initiated and carry no XSRF cookie
      # by design — they MUST bypass XSRF. They are unauthenticated by
      # spec; rate-limit at the reverse-proxy layer.
      def check_xsrf_cookie(self):
          return

      async def post(self):
          try:
              body = self.request.body.decode('utf-8', errors='replace')
              report = json.loads(body or '{}').get('csp-report', {})
          except (ValueError, AttributeError):
              report = {'raw': self.request.body[:512]}
          logging.warning('CSP violation: %s', report)
          self.set_status(204)
          self.finish()
  ```

- [ ] **Step 4: Wire the URL** in `motioneye/server.py` `handler_mapping`: `('/csp-report/?', CspReportHandler)`.

- [ ] **Step 5: Append `report-uri /csp-report` to the CSP header** in `BaseHandler.finish` (keep `report-uri` for compat; a follow-up may also add `Report-To` and `report-to <group>` for newer browsers).

- [ ] **Step 6: Run all tests, smoke test in browser.** Trigger a deliberate violation by injecting an inline `<script>` tag via DevTools and confirm a warning log appears in the server.

- [ ] **Step 7: Commit.**

---

## Phase 3: Lint guard for inline event handlers

### Task 3.1: Add a pre-commit / CI grep that fails on new `on[a-z]+="..."` attributes

**Files:** Create `scripts/check_inline_handlers.sh`, modify `.github/workflows/ci.yml` (or pre-commit config)

- [ ] **Step 1: Write the script.**

  Create `scripts/check_inline_handlers.sh`:
  ```bash
  #!/usr/bin/env bash
  # Fails if any HTML template introduces inline event handlers (which
  # require 'unsafe-inline' in CSP script-src). Run in CI and pre-commit.
  set -euo pipefail
  matches=$(grep -rnE '\bon(click|mouse[a-z]*|change|load|key[a-z]*|focus|blur|submit|input|drag[a-z]*|drop|error)\s*=' motioneye/templates/ || true)
  if [[ -n "$matches" ]]; then
      echo "ERROR: inline event handlers found (incompatible with CSP):"
      echo "$matches"
      echo "Bind the handler from JS instead."
      exit 1
  fi
  ```

- [ ] **Step 2: `chmod +x scripts/check_inline_handlers.sh`** and run it locally. Expected: pass on clean tree.

- [ ] **Step 3: Add a CI step** in `.github/workflows/ci.yml` after the pytest job:
  ```yaml
      - name: Check for inline event handlers
        run: bash scripts/check_inline_handlers.sh
  ```

- [ ] **Step 4: Add to pre-commit** in `.pre-commit-config.yaml` (create if missing) as a `local` hook so contributors catch this before push.

- [ ] **Step 5: Commit.**

### Task 3.2: Add a unit test for inline-handler absence

**Files:** Create `tests/test_templates_csp.py`

- [ ] **Step 1: Write the test.**

  ```python
  import glob
  import re
  import unittest


  HANDLER_RE = re.compile(
      r'\bon(?:click|mouse[a-z]*|change|load|key[a-z]*|focus|blur|'
      r'submit|input|drag[a-z]*|drop|error)\s*=',
      re.IGNORECASE,
  )


  class TemplatesCspTest(unittest.TestCase):
      def test_no_inline_event_handlers(self):
          offenders = []
          for path in glob.glob('motioneye/templates/*.html'):
              with open(path) as f:
                  for n, line in enumerate(f, 1):
                      if HANDLER_RE.search(line):
                          offenders.append(f'{path}:{n}: {line.strip()}')
          self.assertEqual([], offenders,
              'inline event handlers break CSP; bind via JS')


  if __name__ == '__main__':
      unittest.main()
  ```

- [ ] **Step 2: Run, expect pass on current tree.**

- [ ] **Step 3: Commit.**

---

## Phase 4: Browser-driven CI smoke test

### Task 4.1: Add a Playwright-based CI job that hits the running server and asserts zero console errors

**Files:** Create `tests/e2e/test_csp_clean.py`, modify `.github/workflows/ci.yml`

- [ ] **Step 1: Add Playwright as a dev dependency** in `setup.cfg` under a new `[options.extras_require]` section `e2e = playwright>=1.40`. Document `pip install -e .[e2e] && playwright install chromium` in DEVELOPMENT.md.

- [ ] **Step 2: Write the test.**

  ```python
  # tests/e2e/test_csp_clean.py
  import os
  import subprocess
  import time
  import unittest

  import pytest
  from playwright.sync_api import sync_playwright


  @pytest.mark.skipif(
      'CI_E2E' not in os.environ,
      reason='set CI_E2E=1 to run end-to-end CSP smoke',
  )
  class CspCleanTest(unittest.TestCase):
      def setUp(self):
          self.server = subprocess.Popen(
              ['motioneye_env/bin/python', '-m', 'motioneye.meyectl', 'startserver'],
              env={**os.environ,
                   'MOTIONEYE_CONF_PATH': '/tmp/motioneye-e2e/conf',
                   'MOTIONEYE_RUN_PATH': '/tmp/motioneye-e2e/run',
                   'MOTIONEYE_LOG_PATH': '/tmp/motioneye-e2e/log',
                   'MOTIONEYE_MEDIA_PATH': '/tmp/motioneye-e2e/media'},
          )
          time.sleep(5)

      def tearDown(self):
          self.server.terminate()
          self.server.wait(timeout=10)

      def test_landing_page_no_csp_violations(self):
          with sync_playwright() as p:
              browser = p.chromium.launch()
              ctx = browser.new_context()
              page = ctx.new_page()
              errors = []
              page.on('pageerror', lambda e: errors.append(str(e)))
              page.on('console', lambda msg: (
                  errors.append(msg.text)
                  if msg.type == 'error' and 'Content Security' in msg.text
                  else None))
              page.goto('http://localhost:8765/')
              page.wait_for_load_state('networkidle')
              browser.close()
              self.assertEqual([], errors,
                  f'console errors found: {errors}')
  ```

- [ ] **Step 3: Add a CI job** (separate from the unit-test job because Playwright requires browser install) gated on a `[skip-e2e]` PR label or branch protection rule.

- [ ] **Step 4: Run the test locally.** Expected: zero violations.

- [ ] **Step 5: Commit.**

---

## Phase 5: Production deployment checklist

### Task 5.1: Update DEVELOPMENT.md / docs with CSP expectations

**Files:** `DEVELOPMENT.md`, `docs/INSTALLATION.md`

- [ ] **Step 1: Document the CSP policy** — what is allowed, what is not, how to add a new inline script (use the nonce), how to add a new translation that contains HTML (don't — use `.text()`).

- [ ] **Step 2: Document the env-var matrix** the audit added (`MOTIONEYE_RUN_PATH`, `MOTIONEYE_LOG_PATH`, `CA_BUNDLE_PATH`).

- [ ] **Step 3: Document the reverse-proxy expectations**: behind nginx/Caddy, configure HSTS at the proxy (HTTPS termination there), forward `X-Forwarded-Proto` so `self.request.protocol == 'https'` evaluates correctly for the HSTS guard.

- [ ] **Step 4: Commit.**

### Task 5.2: Add deployment-time CSP report-only mode toggle

**Files:** `motioneye/settings.py`, `motioneye/handlers/base.py`

- [ ] **Step 1:** Add `CSP_REPORT_ONLY = False` to `settings.py` (default off in prod, on in staging).

- [ ] **Step 2:** In `BaseHandler.finish`, when `settings.CSP_REPORT_ONLY`, emit the header as `Content-Security-Policy-Report-Only` instead of `Content-Security-Policy`. This lets ops roll out the strict CSP to a staging environment, observe violations via the report endpoint from Task 2.2, then flip to enforcing mode in production.

- [ ] **Step 3:** Test, commit.

---

## Phase 6: Final regression sweep

- [ ] Run `motioneye_env/bin/python -m pytest tests/`. Expected: every Phase 1-5 test passes.
- [ ] Re-run the manual browser smoke from Phase 1, plus exercise: add camera, delete camera, change settings, view live stream, view recordings, log out, log back in.
- [ ] Push branch, open PR referencing this plan and the 2026-05-03 audit plan as parents.

---

## Risk & rollback

- **Loosening `frame-ancestors` to `'self'`** trades a small amount of strictness for functionality. Cross-origin clickjacking remains blocked (the only weakening is intentional same-origin framing). Rollback: change `'self'` back to `'none'` and accept the broken login modal — not advised.
- **CSP nonce regeneration** is per-request and 18 random bytes (144 bits) — collision-resistant for any practical traffic. Rollback path: drop the nonce, fall back to `'unsafe-inline'` (gives up most XSS defence) only as an emergency lever.
- **CSP report-only mode** (Task 5.2) lets ops safely audit before enforcing in production.
