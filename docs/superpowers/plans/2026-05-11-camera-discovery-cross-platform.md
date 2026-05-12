# Cross-Platform Camera Discovery & UI Gating

> **Sub-skill:** Use superpowers:subagent-driven-development or executing-plans to implement task-by-task.

**Goal:** Make the "Add Camera" dialog show the right options on each supported host (regular Linux, Raspberry Pi, macOS) instead of the current all-or-nothing gating on `has_motion`. This is a custom fork — the upstream MotionEye was Pi-centric, but this fork's stated targets include Linux and macOS, and the supporting code (`macoscamctl.py`, the macOS build scripts, the `camctl` import alias) is already half-wired.

**Architecture:**
- **One source of truth** for camera-capability detection: a new `motioneye.platform_caps` module that returns a dict of booleans.
- **Per-option gating** in the template + JS: instead of two coarse flags, each camera-type option in the dropdown has its own flag.
- **Platform-aware labels**: "Local V4L2 Camera" on Linux, "Local AVFoundation Camera" on macOS, "Local Pi Camera" on Pi.
- **Backend already platform-aware** via the `camctl` alias — no daemon-layer rewrite needed.

**Tech Stack:** Python 3.9+, Tornado, jQuery UI. Existing modules: `motioneye/controls/v4l2ctl.py` (Linux), `macoscamctl.py` (macOS via ffmpeg/AVFoundation), `mmalctl.py` (Pi via vcgencmd).

---

## Phase 1: Centralized capability detection

### Task 1.1: New `motioneye.platform_caps` module

**Files:**
- Create `motioneye/platform_caps.py`
- Create `tests/test_platform_caps.py`

- [ ] **Step 1: Write failing test.**

  ```python
  # tests/test_platform_caps.py
  import sys
  import unittest
  from unittest.mock import patch

  from motioneye import platform_caps


  class PlatformCapsTest(unittest.TestCase):
      def test_returns_required_keys(self):
          caps = platform_caps.detect()
          for k in ('has_motion', 'has_v4l2', 'has_avfoundation',
                    'has_mmal', 'has_netcam', 'is_linux', 'is_macos',
                    'is_raspberry_pi'):
              self.assertIn(k, caps)

      def test_macos_flags(self):
          with patch.object(sys, 'platform', 'darwin'):
              caps = platform_caps.detect(force_refresh=True)
          self.assertTrue(caps['is_macos'])
          self.assertFalse(caps['is_linux'])
          self.assertFalse(caps['has_v4l2'])  # no /dev/video* on macOS
          self.assertFalse(caps['has_mmal'])

      def test_linux_non_pi(self):
          with patch.object(sys, 'platform', 'linux'), \
               patch('os.path.exists', side_effect=lambda p: p == '/dev/video0'):
              caps = platform_caps.detect(force_refresh=True)
          self.assertTrue(caps['is_linux'])
          self.assertFalse(caps['is_raspberry_pi'])
          # v4l2 enumeration is the V4L2 backend's job; here we just expose
          # 'platform supports V4L2' = is_linux
          self.assertTrue(caps['has_v4l2'])
  ```

- [ ] **Step 2: Run test — expect failure (module missing).**

  Run: `motioneye_env/bin/python -m pytest tests/test_platform_caps.py -v`
  Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement the module.**

  ```python
  # motioneye/platform_caps.py
  """Single source of truth for what camera backends the host can drive.

  Used by handlers/main.py to populate the template context that gates
  the camera-type options in the Add Camera dialog. Backend modules
  (v4l2ctl, macoscamctl, mmalctl) still self-filter — this module is
  only about *what UI options to show*, not *what devices exist*.
  """
  import os
  import sys

  _cache = None


  def _detect_raspberry_pi() -> bool:
      try:
          with open('/proc/device-tree/model', 'r') as f:
              return 'raspberry pi' in f.read().lower()
      except (FileNotFoundError, PermissionError, OSError):
          return False


  def detect(force_refresh: bool = False) -> dict:
      global _cache
      if _cache is not None and not force_refresh:
          return _cache

      from motioneye import motionctl

      is_linux = sys.platform.startswith('linux')
      is_macos = sys.platform == 'darwin'
      is_pi = is_linux and _detect_raspberry_pi()

      _cache = {
          'is_linux': is_linux,
          'is_macos': is_macos,
          'is_raspberry_pi': is_pi,
          # Local camera backends
          'has_v4l2': is_linux,                 # any Linux: V4L2 API
          'has_mmal': is_pi,                    # Pi only: legacy MMAL stack
          'has_avfoundation': is_macos,         # macOS: ffmpeg + AVFoundation
          # Motion daemon — needed for both netcam (RTSP/HTTP processing)
          # and local V4L2/MMAL capture
          'has_motion': bool(motionctl.find_motion()[0]),
          # netcam requires Motion to do the detection pipeline
          'has_netcam': bool(motionctl.find_motion()[0]),
      }
      return _cache


  def invalidate() -> None:
      """Clear the cache. Used by tests."""
      global _cache
      _cache = None
  ```

- [ ] **Step 4: Run test — expect pass.** (Three tests should pass; if `detect_raspberry_pi` opens `/proc/...` on macOS, ensure the FileNotFoundError path handles it cleanly.)

- [ ] **Step 5: Commit.**

  ```
  feat: motioneye.platform_caps centralized capability detection

  Replaces the coarse has_motion flag with a per-backend capability
  dict (has_v4l2, has_mmal, has_avfoundation, has_netcam, has_motion)
  plus platform flags (is_linux, is_macos, is_raspberry_pi).

  Detection rules:
  - V4L2:        any Linux
  - MMAL:        Pi only, via /proc/device-tree/model
  - AVFoundation: macOS only
  - netcam:      requires Motion daemon (any OS)
  - Motion:      `which motion` succeeds

  Cached after first call; tests call invalidate() between cases.
  ```

---

## Phase 2: Wire capabilities into the UI

### Task 2.1: Pass per-option flags into the main template

**Files:**
- Modify `motioneye/handlers/main.py`
- Modify `motioneye/templates/main.html` (lines 94-95 + neighbours)
- Modify `motioneye/static/js/main.js` (line 4028-4032 dropdown construction)

- [ ] **Step 1: Update `MainHandler.get` to pass the cap dict.**

  Replace lines 50-60 (the `has_h264_*` flags can stay; we're only changing the camera-type gating):

  ```python
  from motioneye import platform_caps
  caps = platform_caps.detect()

  self.render(
      'main.html',
      ...,
      camera_caps=caps,  # NEW
      # Keep has_motion for backward compat with any other template ref
      has_motion=caps['has_motion'],
      ...
  )
  ```

- [ ] **Step 2: Update `main.html` (around lines 94-95).**

  ```html
  // OLD
  var hasLocalCamSupport = {% if has_motion %}true{% else %}false{% endif %};
  var hasNetCamSupport   = {% if has_motion %}true{% else %}false{% endif %};

  // NEW
  var cameraCaps = {
      v4l2:          {% if camera_caps.has_v4l2 and camera_caps.has_motion %}true{% else %}false{% endif %},
      mmal:          {% if camera_caps.has_mmal and camera_caps.has_motion %}true{% else %}false{% endif %},
      avfoundation:  {% if camera_caps.has_avfoundation and camera_caps.has_motion %}true{% else %}false{% endif %},
      netcam:        {% if camera_caps.has_netcam %}true{% else %}false{% endif %},
      motioneye:     true,
      mjpeg:         true,
      isMacos:       {% if camera_caps.is_macos %}true{% else %}false{% endif %},
      isLinux:       {% if camera_caps.is_linux %}true{% else %}false{% endif %},
      isPi:          {% if camera_caps.is_raspberry_pi %}true{% else %}false{% endif %}
  };
  // Compatibility shims for any other code that still reads the old flags
  var hasLocalCamSupport = cameraCaps.v4l2 || cameraCaps.mmal || cameraCaps.avfoundation;
  var hasNetCamSupport   = cameraCaps.netcam;
  ```

- [ ] **Step 3: Update the dropdown construction in `main.js:4028-4032`.**

  ```js
  // OLD
  (hasLocalCamSupport ? '<option value="v4l2">'+i18n.gettext("Loka V4L2-kamerao")+'</option>' : '') +
  (hasLocalCamSupport ? '<option value="mmal">'+i18n.gettext("Loka MMAL-kamerao")+'</option>' : '') +
  (hasNetCamSupport   ? '<option value="netcam">'+i18n.gettext("Reta kamerao")+'</option>'    : '') +
                        '<option value="motioneye">'+i18n.gettext("Fora motionEye kamerao")+'</option>' +
                        '<option value="mjpeg">'+i18n.gettext("Simpla MJPEG-kamerao")+'</option>'

  // NEW
  (cameraCaps.v4l2         ? '<option value="v4l2">'        +i18n.gettext("Local USB / V4L2 Camera")     +'</option>' : '') +
  (cameraCaps.mmal         ? '<option value="mmal">'        +i18n.gettext("Local Pi Camera (CSI/MMAL)")  +'</option>' : '') +
  (cameraCaps.avfoundation ? '<option value="v4l2">'        +i18n.gettext("Local Camera (built-in/USB)") +'</option>' : '') +
  (cameraCaps.netcam       ? '<option value="netcam">'      +i18n.gettext("Network / IP Camera")         +'</option>' : '') +
                             '<option value="motioneye">'   +i18n.gettext("Remote motionEye Camera")     +'</option>' +
                             '<option value="mjpeg">'       +i18n.gettext("Simple MJPEG Camera")         +'</option>'
  ```

  **Note on the macOS option `value`:** keep it `"v4l2"` because downstream code in `runAddCameraDialog` and the Motion config builder branch on `typeSelect.val() == 'v4l2'`. The `camctl` alias in `config.py` and `handlers/config.py` is already platform-aware — calling `camctl.list_devices()` on macOS routes to `macoscamctl` and returns AVFoundation devices. So the `value` stays the same; only the label changes.

- [ ] **Step 4: Run unit tests and start the server.**

  ```
  motioneye_env/bin/python -m pytest tests/
  lsof -ti:8765 | xargs kill 2>/dev/null; sleep 2
  MOTIONEYE_CONF_PATH=/tmp/motioneye-test/conf \
    MOTIONEYE_RUN_PATH=/tmp/motioneye-test/run \
    MOTIONEYE_LOG_PATH=/tmp/motioneye-test/log \
    MOTIONEYE_MEDIA_PATH=/tmp/motioneye-test/media \
    motioneye_env/bin/python -m motioneye.meyectl startserver -d &
  ```

  Expected: dropdown shows just "Remote motionEye Camera" and "Simple MJPEG Camera" if Motion is not installed (V4L2/MMAL/AVFoundation/netcam all gated on `has_motion`).

- [ ] **Step 5: Commit.**

---

## Phase 3: Install Motion locally and verify

### Task 3.1: Build/install Motion via the repo's own script

**Files:** none (uses existing `build/install_macos.sh`)

- [ ] **Step 1:** Run `./build/install_macos.sh`. This installs to `/opt/motioneye-lite/bin/motion`.

- [ ] **Step 2:** Wire the binary by setting `settings.MOTION_BINARY` or adding to `PATH`. Verify with `motioneye_env/bin/python -c "from motioneye.motionctl import find_motion; print(find_motion())"`. Expected: `('/opt/motioneye-lite/bin/motion', 'X.Y.Z')`.

- [ ] **Step 3:** Restart server, reload the Add Camera dialog. Expected:
  - On macOS: "Local Camera (built-in/USB)", "Network / IP Camera", "Remote motionEye Camera", "Simple MJPEG Camera"
  - On Linux non-Pi: same but "Local USB / V4L2 Camera" instead of "Local Camera (built-in/USB)"
  - On Pi: both V4L2 and "Local Pi Camera (CSI/MMAL)"

- [ ] **Step 4:** For each visible option, exercise the device-list fetch (the camera-type select's `change` handler hits `/config/list/`). Confirm devices populate.

- [ ] **Step 5:** Document the install path in DEVELOPMENT.md.

---

## Phase 4: Tests + CI for the gating

### Task 4.1: HandlerTestCase exercising the camera-caps render path

**Files:** Create `tests/test_handlers/test_main_caps.py`

- [ ] **Step 1: Write the test.**

  ```python
  from unittest.mock import patch
  from motioneye.handlers.main import MainHandler
  from tests.test_handlers import HandlerTestCase


  class MainCapsTest(HandlerTestCase):
      handler_cls = MainHandler

      def test_main_renders_camera_caps_into_template(self):
          fake_caps = {
              'is_linux': False, 'is_macos': True, 'is_raspberry_pi': False,
              'has_v4l2': False, 'has_mmal': False,
              'has_avfoundation': True, 'has_netcam': True,
              'has_motion': True,
          }
          with patch('motioneye.platform_caps.detect', return_value=fake_caps):
              response = self.fetch('/')
          self.assertEqual(200, response.code)
          body = response.body.decode()
          # The template injects the caps as a JS object literal
          self.assertIn('avfoundation:  true', body)
          self.assertIn('v4l2:          false', body)

      def test_no_motion_hides_local_and_netcam(self):
          fake_caps = {
              'is_linux': True, 'is_macos': False, 'is_raspberry_pi': False,
              'has_v4l2': True, 'has_mmal': False,
              'has_avfoundation': False, 'has_netcam': False,
              'has_motion': False,
          }
          with patch('motioneye.platform_caps.detect', return_value=fake_caps):
              response = self.fetch('/')
          body = response.body.decode()
          self.assertIn('v4l2:          false', body)  # gated on has_motion AND
          self.assertIn('netcam:        false', body)
  ```

- [ ] **Step 2:** Run, expect failure (current template doesn't render `camera_caps` JS object).

- [ ] **Step 3:** Fix the template if needed so the test passes.

- [ ] **Step 4:** Commit.

---

## Phase 5: Documentation

### Task 5.1: Update DEVELOPMENT.md / README.md

- [ ] **Step 1:** Add a "Supported camera types" matrix to the README, plus install commands per platform.

  | Camera type | macOS | Linux (any) | Raspberry Pi |
  |---|---|---|---|
  | Built-in / USB (AVFoundation) | ✅ | — | — |
  | USB / V4L2 | — | ✅ | ✅ |
  | Pi CSI Module (MMAL) | — | — | ✅ |
  | Network / IP (RTSP, HTTP, ONVIF) | ✅ | ✅ | ✅ |
  | Remote motionEye | ✅ | ✅ | ✅ |
  | Simple MJPEG (proxy) | ✅ | ✅ | ✅ |

- [ ] **Step 2:** Document `MOTION_BINARY` setting and how to point it at a custom build (e.g., `/opt/motioneye-lite/bin/motion` on macOS).

- [ ] **Step 3:** Commit.

---

## Risk & rollback

- **The dropdown label change is purely cosmetic** — the option `value` stays the same, so existing camera configs and the Motion config builder are unaffected.
- **The cap dict is cached** after first call. Restart the server to re-detect (e.g., after installing Motion). `platform_caps.invalidate()` is exposed for testing.
- **Per-option gating is additive**: anything we now hide was already hidden by the old `has_motion` flag. So no platform that used to work will lose options.
- **Pi detection** reads `/proc/device-tree/model` which is unprivileged-readable on Pi OS. Failure → `is_raspberry_pi=False`, falling back to the V4L2 path (which works on Pi too).

## Self-review

- All template substitutions use `{% if ... %}true{% else %}false{% endif %}` to avoid JSON injection from Python booleans.
- Tests use `invalidate()` between cases so caching doesn't leak.
- The `value="v4l2"` reuse for AVFoundation is intentional — relies on the existing `camctl` alias in config.py / handlers/config.py / server.py.
