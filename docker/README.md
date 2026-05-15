# docker/

This directory contains the Dockerfile and Compose files used to build
and run MotionEye Custom in a container.

**The full Docker deployment guide is in
[`../docs/DOCKER.md`](../docs/DOCKER.md)** — quick start, Compose,
multi-arch builds, USB camera passthrough, backup/restore, and
troubleshooting.

## Files in this directory

| File | Purpose |
|---|---|
| `Dockerfile` | Image definition; multi-arch (amd64 + arm64) |
| `docker-compose.yml` | Base Compose service definition |
| `docker-compose.override.yml` | Example host overrides (USB camera pass-through) — Compose auto-loads this |
| `entrypoint.sh` | Container entrypoint (handles init + UID/GID mapping) |
| `motioneye-docker.conf` | Default config template baked into the image |

## Quick build

```bash
# From the repo root:
docker build -t im1k31s/motioneye-custom:dev -f docker/Dockerfile .
docker compose -f docker/docker-compose.yml up -d
```

For everything else — published image tags, multi-arch builds,
camera device passthrough, runtime tuning — see
[`../docs/DOCKER.md`](../docs/DOCKER.md).
