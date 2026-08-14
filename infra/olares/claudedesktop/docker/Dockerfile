# syntax=docker/dockerfile:1
#
# Claude Desktop (Linux) on a browser-streamed X11 desktop, for Olares.
#
# Anthropic ships the Linux desktop app as a .deb from its own apt repository
# (Ubuntu 22.04+ / Debian 12+, amd64 + arm64). The app is a native GUI, so it
# needs a display: baseimage-selkies supplies openbox on Xvfb plus the Selkies
# WebRTC/websocket streamer and an nginx front end on ports 3000/3001, with
# $HOME set to the /config volume.
#
# The .deb is installed at build time rather than at pod start: it writes to
# /usr/lib and /usr/bin, which are outside the app's persistent volume, so a
# runtime install would need a root init container and would repeat on every
# start. Pinning here also makes the image reproducible and lets Chart.appVersion
# describe exactly what a given tag contains.
#
# Build & push (multi-arch, matches spec.supportArch):
#   docker buildx create --use --name claudedesktop-builder || true
#   docker buildx build \
#     --platform linux/amd64,linux/arm64 \
#     --build-arg CLAUDE_DESKTOP_VERSION=1.28929.0 \
#     -t ghcr.io/jasonlswenson-sys/claude-desktop-olares:1.28929.0-selkies1 \
#     --push .

FROM ghcr.io/linuxserver/baseimage-selkies:ubuntunoble

# Version of the `claude-desktop` package to pin. Must match Chart.appVersion
# and spec.versionName in OlaresManifest.yaml.
ARG CLAUDE_DESKTOP_VERSION=1.28929.0
ARG BUILD_DATE
ARG VERSION

LABEL build_version="claude-desktop:${CLAUDE_DESKTOP_VERSION} image:${VERSION} build-date:${BUILD_DATE}"
LABEL org.opencontainers.image.title="Claude Desktop for Olares"
LABEL org.opencontainers.image.description="Anthropic's Claude desktop app for Linux on a Selkies-streamed X11 desktop"
LABEL org.opencontainers.image.source="https://github.com/APEX-Power-Ops/apex-power-ops-platform"

# TITLE names the browser tab and the openbox window. The base image defaults to
# a Wayland compositor; Claude Desktop's Electron build mis-scales there under
# the Olares entrance proxy, so pin X11. The chart sets the same value so the
# behaviour is visible in the workload spec too.
ENV TITLE="Claude" \
    PIXELFLUX_WAYLAND=false

# Fingerprint of Anthropic's package signing key, from
# https://code.claude.com/docs/en/desktop-linux. Verified below so a wrong or
# truncated key download fails the build instead of silently trusting whatever
# was served.
ENV CLAUDE_DESKTOP_KEY_FINGERPRINT=31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE

RUN \
  echo "**** install runtime dependencies ****" && \
  apt-get update && \
  apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    fonts-liberation \
    libnotify4 \
    libsecret-1-0 \
    xdg-utils && \
  echo "**** add anthropic apt repository ****" && \
  curl -fsSLo /usr/share/keyrings/claude-desktop-archive-keyring.asc \
    https://downloads.claude.ai/claude-desktop/key.asc && \
  gpg --show-keys --with-colons /usr/share/keyrings/claude-desktop-archive-keyring.asc \
    | grep -qx "fpr:::::::::${CLAUDE_DESKTOP_KEY_FINGERPRINT}:" && \
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/claude-desktop-archive-keyring.asc] https://downloads.claude.ai/claude-desktop/apt/stable stable main" \
    > /etc/apt/sources.list.d/claude-desktop.list && \
  echo "**** install claude-desktop ${CLAUDE_DESKTOP_VERSION} ****" && \
  apt-get update && \
  apt-get install -y --no-install-recommends \
    "claude-desktop=${CLAUDE_DESKTOP_VERSION}" && \
  echo "**** reuse the app's own icon for the streamed desktop ****" && \
  for size in 512x512 256x256 128x128; do \
    src="/usr/share/icons/hicolor/${size}/apps/claude-desktop.png"; \
    if [ -f "$src" ]; then cp "$src" /usr/share/selkies/www/icon.png && break; fi; \
  done && \
  echo "**** cleanup ****" && \
  apt-get autoclean && \
  rm -rf \
    /config/.cache \
    /var/lib/apt/lists/* \
    /var/tmp/* \
    /tmp/*

# autostart, openbox menu entry, and the launch wrapper
COPY root/ /

EXPOSE 3000 3001

VOLUME /config
