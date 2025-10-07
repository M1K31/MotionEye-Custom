FROM debian:trixie-slim
LABEL maintainer="Marcus Klein <himself@kleini.org>"

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
      'armhf'|'riscv64') PACKAGES='python3-dev gcc libjpeg62-turbo-dev libcurl4-openssl-dev libssl-dev';; \
      *) PACKAGES='';; \
    esac && \
    apt-get -q update && \
    DEBIAN_FRONTEND="noninteractive" apt-get -qq --option Dpkg::Options::="--force-confnew" --no-install-recommends install \
      ca-certificates curl python3 fdisk $PACKAGES && \
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

# Set runtime user (after motion user is created)
USER motion:motion
WORKDIR /app

# R/W needed for motionEye to update configurations
VOLUME /etc/motioneye

# Video & images
VOLUME /var/lib/motioneye

EXPOSE 8765

ENTRYPOINT ["/entrypoint.sh"]
