FROM debian:trixie-slim
LABEL org.opencontainers.image.title="motionEye Custom" \
      org.opencontainers.image.description="Web frontend for the Motion video surveillance daemon (custom fork)" \
      org.opencontainers.image.source="https://github.com/M1K31/MotionEye-Custom" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.authors="im1k31s, upstream: Marcus Klein <himself@kleini.org>"

# Build arguments for user/group IDs
ARG RUN_UID=1000
ARG RUN_GID=1000

# Copy application source and entrypoint
COPY . /tmp/motioneye
COPY docker/entrypoint.sh /entrypoint.sh

# Configure pip to allow system-wide package installation
RUN printf '%b' '[global]\nbreak-system-packages=true\n' > /etc/pip.conf

# Install system dependencies and build application
RUN case "$(dpkg --print-architecture)" in \
      'armhf'|'arm64'|'riscv64') PACKAGES='python3-dev gcc cmake build-essential libjpeg62-turbo-dev libcurl4-openssl-dev libssl-dev';; \
      *) PACKAGES='python3-dev gcc cmake build-essential';; \
    esac && \
    apt-get -q update && \
    DEBIAN_FRONTEND="noninteractive" apt-get -qq --option Dpkg::Options::="--force-confnew" --no-install-recommends install \
      ca-certificates curl python3 fdisk procps $PACKAGES && \
    curl -sSfO 'https://bootstrap.pypa.io/get-pip.py' && \
    python3 get-pip.py && \
    python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir /tmp/motioneye && \
    motioneye_init --skip-systemd --skip-apt-update && \
    # Configure motion user with desired UID/GID
    sed -i "s/^\(motion:[^:]*\):[0-9]*:[0-9]*:\(.*\)/\1:${RUN_UID}:${RUN_GID}:\2/" /etc/passwd && \
    sed -i "s/^\(motion:[^:]*\):[0-9]*:\(.*\)/\1:${RUN_GID}:\2/" /etc/group && \
    # Set up configuration and data directories
    mv /etc/motioneye/motioneye.conf /etc/motioneye.conf.sample && \
    mkdir /var/log/motioneye /var/lib/motioneye && \
    chown motion:motion /var/log/motioneye /var/lib/motioneye && \
    # Security cleanup - remove SUID/SGID binaries
    find / -type f \( -perm -4000 -o -perm -2000 \) -delete 2>/dev/null || true && \
    # Package cleanup
    python3 -m pip uninstall -y pip setuptools wheel && \
    DEBIAN_FRONTEND="noninteractive" apt-get -qq autopurge $PACKAGES && \
    apt-get clean && \
    rm -r /var/lib/apt/lists /var/cache/apt /tmp/motioneye get-pip.py /root/.cache

# NOTE: the container intentionally starts as root so entrypoint.sh
# can create /run/motioneye and chown root-mounted volumes; it then
# drops to the unprivileged `motion` user via `su` before exec'ing
# the server. Do NOT add `USER motion:motion` here — that would run
# the entrypoint unprivileged and the mkdir/chown would fail with
# "Permission denied".
WORKDIR /app

# Health check to monitor container status
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8765/ || exit 1

# R/W needed for motionEye to update configurations
VOLUME /etc/motioneye

# Video & images
VOLUME /var/lib/motioneye

EXPOSE 8765

ENTRYPOINT ["/entrypoint.sh"]
