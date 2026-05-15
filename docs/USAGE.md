# Usage Guide

Day-to-day operation of MotionEye Custom after installation. For
install paths, see [`INSTALLATION.md`](INSTALLATION.md).

---

## Accessing the web interface

Default URL: <http://localhost:8765/>

On first boot you'll see the **Set Admin Password** modal — this is
the bootstrap flow (`@force_password_change=true` until you save a
password). After setting it, log out / log back in any time using the
**Login** dialog at the same URL.

---

## Starting and stopping

### Docker

```bash
docker start motioneye         # start
docker stop motioneye          # stop
docker restart motioneye       # restart
docker logs -f motioneye       # follow logs
docker stats motioneye         # resource usage
```

### Linux (systemd)

```bash
sudo systemctl start motioneye
sudo systemctl stop motioneye
sudo systemctl restart motioneye
sudo systemctl enable motioneye      # auto-start at boot
journalctl -fu motioneye             # follow logs
```

### macOS — Lite

```bash
/opt/motioneye-lite/bin/meyectl startserver           # foreground
nohup /opt/motioneye-lite/bin/meyectl startserver \
  > /tmp/motioneye.log 2>&1 &                         # background
pkill -f motioneye                                    # stop
```

### macOS / Linux — virtualenv install

```bash
source ~/motioneye-env/bin/activate
python -m motioneye.meyectl startserver               # foreground
python -m motioneye.meyectl startserver --debug       # debug logs
```

---

## Adding cameras

1. Click **"You have not configured any camera yet. Click here to add
   one..."** (or the camera dropdown → "Add Camera" if any cameras
   are already configured).
2. Pick the **Camera Type**. Only options compatible with the host
   show up:
   - **Built-in or USB Camera (AVFoundation)** — macOS native + USB
     webcams. macOS will prompt for camera permission on first
     stream start (System Settings → Privacy & Security → Camera).
   - **USB Webcam (V4L2)** — Linux `/dev/video*` devices.
   - **Raspberry Pi Camera Module (MMAL)** — CSI-attached cameras
     on Pi (legacy MMAL stack).
   - **IP / Network Camera (RTSP, HTTP, ONVIF)** — any camera that
     exposes a stream URL. Check the camera vendor's manual for the
     exact path.
   - **Remote motionEye Camera** — relay another motionEye instance.
   - **MJPEG Stream Proxy** — direct MJPEG passthrough (no motion
     detection; the Motion daemon is not required for this option).
3. Fill in URL / credentials as prompted, pick the device from the
   "Camera" dropdown, click **OK**.
4. The new camera appears in the header dropdown. Click **Apply** to
   persist.

---

## Motion detection

In the camera settings panel:

1. Open **Motion Detection**.
2. **Threshold** — number of changed pixels needed to trigger
   detection. Higher value = less sensitive.
3. **Noise Level** — auto by default; lower for cleaner video.
4. **Frame Change Threshold** — percentage of frame that must change.
5. **Mask** — paint regions to ignore (e.g., trees that wave in wind).

After tweaking, **Apply** to save.

---

## Facial recognition (optional)

Requires the optional `face_recognition` extra, which pulls in the
heavy `dlib` dependency:

```bash
pip install motioneye[face_recognition]
```

The default Docker image does **not** bundle `face_recognition` (it
would roughly double the image size). To use it in Docker, build a
derived image:

```dockerfile
FROM im1k31s/motioneye-custom:latest
# The base image runs its entrypoint as root and drops to the
# `motion` user itself — do not add a USER directive here.
RUN python3 -m pip install --no-cache-dir --break-system-packages \
    'face_recognition>=1.3,<2.0'
```

### Enable for a camera

1. Open camera settings → **Motion Detection**.
2. Tick **Enable OpenCV Analysis**.
3. Apply.

Every motion-triggered picture now runs through OpenCV face
detection.

### Manage familiar faces

1. Main settings → **Familiar Faces** → **Manage Faces**.
2. Upload a clear front-facing image (JPG or PNG) per person; the
   filename you provide becomes the label (e.g., `Jules`).
3. Delete faces from the same panel.

When a detected face matches no familiar entry, the log records
"Unfamiliar Person".

---

## Home Assistant integration (MQTT)

MotionEye Custom publishes motion sensors via MQTT Discovery.

1. Main settings → **MQTT Integration** (enable Advanced Settings if
   the section is hidden).
2. **Enable** the integration; fill in broker address, port (default
   `1883`), and username/password if required.
3. Apply. MotionEye restarts and connects.

Home Assistant auto-discovers one entity per camera:

- `binary_sensor.motioneye_camera_<id>_motion` — `on` while motion
  is detected, `off` otherwise. Use this in automations.

### Adding the camera feed to Home Assistant

Use the built-in **MJPEG Camera** integration:

1. Home Assistant → **Settings → Devices & Services → Add Integration**.
2. Search for **MJPEG Camera**.
3. **MJPEG URL** is the "Streaming URL" from motionEye's *Video
   Streaming* section (e.g., `http://192.168.1.5:8081/`).
4. Submit.

### Example automation

```yaml
alias: Notify on front-door motion
trigger:
  - platform: state
    entity_id: binary_sensor.motioneye_camera_1_motion
    to: "on"
action:
  - service: notify.mobile_app_my_phone
    data:
      message: Motion detected at the front door
mode: single
```

---

## Storage

In camera settings → **File Storage**:

- **Storage Device** dropdown lists pre-defined options and
  **Custom Path**.
- Picking **Custom Path** reveals **Root Directory** — enter any
  absolute path on the local filesystem
  (e.g., `/mnt/nas/motion_captures`).
- Ensure the user running motionEye has write permission to the
  chosen directory.

### Retention

In the same panel:

- **Preserve Pictures / Movies** — auto-delete after N days, or keep
  forever.

---

## Performance tuning

Most users won't need this. Settings live in `motion.conf` (typically
`/etc/motioneye/motion.conf`, or `~/motioneye-env/etc/motion.conf`,
or `/etc/motioneye/motion.conf` in the Docker container's
`etc_motioneye` volume).

### `mjpeg_proxy_buffer_size`

- **Default:** `3`
- Frames to buffer in the MJPEG proxy. Larger = smoother on unstable
  networks but more memory per camera.

### `config_cache_ttl`

- **Default:** `30` (seconds)
- How long camera config is cached in memory. Lower = changes made
  by editing the file directly (outside the UI) are picked up
  faster, at a small CPU cost.

### Resilience features (always on)

- **Motion daemon recovery** — if `motion` crashes, motionEye
  restarts it (up to 5 times in quick succession before giving up).
  Linux uses `systemctl`, macOS uses `launchd`.
- **MJPEG client backoff** — connection drops auto-reconnect with
  exponential backoff. No more "stream stuck until restart".
- **Periodic GC** — a background task every 5 minutes runs Python
  garbage collection and warn-logs if RSS exceeds 500 MB.

---

## Updating

### Docker

```bash
docker pull im1k31s/motioneye-custom:latest
docker compose down && docker compose up -d
```

### Native (pip)

```bash
source ~/motioneye-env/bin/activate
pip install --upgrade motioneye
sudo systemctl restart motioneye  # Linux
```

After a security-relevant update (e.g., from the audit-fixes branch),
existing SHA-1 admin passwords keep working; the verifier transparently
upgrades the stored hash to bcrypt on next password change. To force
the upgrade without changing the password, save any other config
setting through the web UI.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Add-camera dropdown only shows Remote motionEye + MJPEG Stream Proxy | Motion daemon not installed | See [`INSTALLATION.md`](INSTALLATION.md) "Installing the Motion daemon" |
| `(no cameras)` listed under "Camera" dropdown on macOS | macOS Camera permission (TCC) not granted | System Settings → Privacy & Security → Camera; or use IP/Network camera |
| Login modal returns every server restart | Cookies cleared or browser blocking them | Click **Remember me** (sets 10-year cookie); enable cookies for `localhost:8765` |
| 403 Forbidden on save | Stale browser session vs new XSRF token | Hard-reload (Cmd-Shift-R / Ctrl-F5) |
| "Refused to execute a script" in console | CSP blocked a third-party script or inline handler | File a bug — all first-party content should be CSP-clean |
| Server fails to start with "pid directory is not writable" | `/var/run` not writable (non-root macOS) | Set `MOTIONEYE_RUN_PATH=/tmp/motioneye/run` |

---

## More

- Detailed install paths: [`INSTALLATION.md`](INSTALLATION.md)
- Docker specifics: [`DOCKER.md`](DOCKER.md)
- macOS native build: [`MOTIONEYE_LITE.md`](MOTIONEYE_LITE.md)
- Removal: [`../UNINSTALL.md`](../UNINSTALL.md)
