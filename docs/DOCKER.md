# Docker Deployment Guide

Recommended deployment path. The image bundles Python, motionEye,
the Motion daemon, and ffmpeg — no host-side build needed.

Official image: **`im1k31s/motioneye-custom`** ([Docker Hub](https://hub.docker.com/r/im1k31s/motioneye-custom))

| Tag | Notes |
|---|---|
| `latest` | most recent release |
| `<version>` (e.g. `0.43.1b4`) | pinned release |
| `edge` | latest commit on `main` (development) |

Multi-arch: **linux/amd64** + **linux/arm64**.

---

## Quick start (`docker run`)

```bash
docker run -d \
  --name motioneye \
  --restart unless-stopped \
  -p 8765:8765 \
  -p 8081:8081 \
  -v motioneye-config:/etc/motioneye \
  -v motioneye-media:/var/lib/motioneye \
  -v /etc/localtime:/etc/localtime:ro \
  im1k31s/motioneye-custom:latest
```

- **8765** — main web UI
- **8081** — first camera stream port (Motion uses
  `8081, 8082, 8083, …` per camera; expose more as you add cameras)
- **/etc/motioneye** — config volume; survives container recreation
- **/var/lib/motioneye** — recordings/snapshots volume

Open <http://localhost:8765/> and set the admin password on first
boot.

---

## Docker Compose (recommended for production)

Create `docker-compose.yml`:

```yaml
services:
  motioneye:
    image: im1k31s/motioneye-custom:latest
    container_name: motioneye
    restart: unless-stopped
    ports:
      - "8765:8765"     # web UI
      - "8081:8081"     # camera 1 stream
      # - "8082:8082"   # camera 2 stream (add as needed)
    volumes:
      - ./config:/etc/motioneye
      - ./media:/var/lib/motioneye
      - /etc/localtime:/etc/localtime:ro
    environment:
      - TZ=America/New_York
    # Optional: pass USB cameras through to the container
    # devices:
    #   - /dev/video0:/dev/video0
    #   - /dev/video1:/dev/video1
```

Start:

```bash
docker compose up -d
docker compose logs -f
```

Stop / update:

```bash
docker compose pull
docker compose up -d           # rolling restart with new image
docker compose down            # stop and remove
```

### `docker-compose.override.yml`

Docker Compose auto-loads a sibling `docker-compose.override.yml`
file if present. Use it for host-specific tweaks (USB cameras,
local volume paths) without touching the main file:

```yaml
services:
  motioneye:
    devices:
      - /dev/video0:/dev/video0
      - /dev/video1:/dev/video1
    volumes:
      - /etc/localtime:/etc/localtime:ro
```

An example `docker-compose.override.yml` ships in the
[`docker/`](../docker/) directory.

---

## Build from source

```bash
git clone https://github.com/M1K31/MotionEye-Custom.git
cd MotionEye-Custom

# Build the image
docker build -t im1k31s/motioneye-custom:dev -f docker/Dockerfile .

# Run it
docker run -d --name motioneye -p 8765:8765 im1k31s/motioneye-custom:dev
```

Or use Compose with `build: .` (uncomment that line in
`docker/docker-compose.yml`).

### Multi-architecture build

```bash
# Set up buildx (one-time)
docker buildx create --name multiarch --use

# Build and push linux/amd64 + linux/arm64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t im1k31s/motioneye-custom:latest \
  --push \
  -f docker/Dockerfile .
```

### Automated publishing (CI)

`.github/workflows/docker-publish.yml` builds and pushes the
multi-arch image automatically:

| Trigger | Tags published |
|---|---|
| push to `main` | `:edge` |
| git tag `vX.Y.Z` | `:X.Y.Z`, `:X.Y`, `:latest` |
| manual dispatch | `:edge` |

It requires two repository secrets (**Settings → Secrets and
variables → Actions**):

- `DOCKER_USERNAME` — `im1k31s`
- `DOCKER_PASSWORD` — a Docker Hub access token with **Read/Write**
  scope, created at <https://app.docker.com/settings> → Personal
  access tokens

Forks skip the workflow automatically (the `if:` guard checks the
repository name) so they don't fail on missing secrets.

---

## Attaching cameras

### IP / RTSP cameras

No special configuration needed — the container reaches them over the
network. Just add them via the web UI.

### USB / V4L2 cameras (Linux host only)

Pass the device into the container:

```yaml
devices:
  - /dev/video0:/dev/video0
```

Or with `docker run`:

```bash
docker run -d \
  --device=/dev/video0:/dev/video0 \
  ... im1k31s/motioneye-custom:latest
```

Check which devices exist:

```bash
ls -la /dev/video*
v4l2-ctl --list-devices       # if v4l-utils is installed
```

### macOS USB cameras

**Not supported via Docker on macOS.** Docker Desktop's Linux VM has
no AVFoundation passthrough. Options:

- Use the IP/Network camera path (point at an RTSP feed)
- Run **motionEye Lite** natively — see
  [`MOTIONEYE_LITE.md`](MOTIONEYE_LITE.md)

### Raspberry Pi CSI camera

Pass through the necessary devices and enable the camera in `raspi-config`:

```yaml
devices:
  - /dev/video0:/dev/video0
  - /dev/vchiq:/dev/vchiq
  - /dev/dma_heap:/dev/dma_heap
group_add:
  - video
```

---

## Common operations

```bash
docker logs -f motioneye                   # follow logs
docker exec -it motioneye bash             # shell into container
docker stats motioneye                     # resource usage
docker restart motioneye                   # restart
docker compose pull && docker compose up -d  # update to latest
```

### Backup config + media

```bash
docker run --rm \
  -v motioneye-config:/source:ro \
  -v "$(pwd)":/backup \
  alpine tar czf /backup/motioneye-config.tar.gz -C /source .

docker run --rm \
  -v motioneye-media:/source:ro \
  -v "$(pwd)":/backup \
  alpine tar czf /backup/motioneye-media.tar.gz -C /source .
```

### Restore

```bash
docker run --rm \
  -v motioneye-config:/target \
  -v "$(pwd)":/backup \
  alpine sh -c "cd /target && tar xzf /backup/motioneye-config.tar.gz"
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Container exits immediately | Volume permissions | Check `docker logs motioneye`; ensure the UID/GID writing to `/etc/motioneye` matches the container's `motion` user (default UID 1000) |
| Health check failing | Server slow to start | First boot can take 30–60s; `HEALTHCHECK` has a 60s `start-period` already |
| `Refused to connect` to camera stream | Port 8081+ not published | Add `- "8081:8081"` (and more for additional cameras) |
| USB camera not visible inside container | Linux only — device not mapped | Add `devices:` block (see "Attaching cameras") |
| ARM64 image pulls slowly / fails | Multi-arch manifest mismatch | Verify `docker manifest inspect im1k31s/motioneye-custom:latest`; pull a specific digest if needed |
| Recordings filling disk | Default retention is "forever" | Set per-camera retention under File Storage; or mount `/var/lib/motioneye` to a host path with quota |

---

## Build args & env vars

| Build arg | Default | Purpose |
|---|---|---|
| `RUN_UID` | `1000` | UID for the `motion` user inside the container — set to match the host UID owning the mounted volumes |
| `RUN_GID` | `1000` | GID for the `motion` user |

```bash
docker build \
  --build-arg RUN_UID=$(id -u) \
  --build-arg RUN_GID=$(id -g) \
  -t im1k31s/motioneye-custom:dev \
  -f docker/Dockerfile .
```

Runtime env vars (set in `environment:` in Compose, or `-e` with
`docker run`):

| Env | Purpose |
|---|---|
| `TZ` | container timezone (e.g., `America/New_York`) |
| `MOTIONEYE_CONF_PATH` | override default `/etc/motioneye` (uncommon) |
| `MOTIONEYE_MEDIA_PATH` | override default `/var/lib/motioneye` (uncommon) |

---

## Docker vs native install

| | Docker | Linux native | macOS native (Lite) |
|---|---|---|---|
| Setup time | 1 min | ~10 min | ~60–120 min build |
| Resource footprint | ~200 MB RAM, 1.6 GB disk | ~50 MB RAM, 100 MB disk | ~50 MB RAM, 150 MB disk |
| USB cameras on macOS | ❌ | n/a | ✅ |
| Easy upgrades | `compose pull` | `pip install -U` | rebuild |
| Multi-host orchestration (k8s, swarm) | ✅ | manual | manual |

Default recommendation: **Docker** unless you specifically need
native macOS USB cameras.

---

## See also

- [`INSTALLATION.md`](INSTALLATION.md) — all install paths
- [`USAGE.md`](USAGE.md) — day-to-day operation
- [`MOTIONEYE_LITE.md`](MOTIONEYE_LITE.md) — macOS native build
