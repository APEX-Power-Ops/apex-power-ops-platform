# claude-desktop-olares image

Container image for the Olares `claudedesktop` app: Anthropic's official Claude
desktop app for Linux on a browser-streamed X11 desktop.

## What it ships

- **Base:** `ghcr.io/linuxserver/baseimage-selkies:ubuntunoble` (Ubuntu 24.04) —
  Xvfb + openbox + the Selkies streamer + nginx on `3000` (HTTP) and `3001`
  (HTTPS), running as uid/gid 1000 with `HOME=/config`.
- **App:** `claude-desktop`, pinned by the `CLAUDE_DESKTOP_VERSION` build arg
  and installed from Anthropic's apt repository at
  `https://downloads.claude.ai/claude-desktop/apt/stable`. The repository's
  signing key is verified against fingerprint
  `31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE` during the build.
- **Runtime deps** the .deb does not pull in on a headless base:
  `fonts-liberation`, `libnotify4`, `libsecret-1-0`, `xdg-utils`.
- **Overlay** (`root/`):
  - `/usr/bin/wrapped-claude-desktop` — clears stale Electron singleton locks,
    then launches with `--no-sandbox` (no user namespaces in the pod) and
    `--password-store=basic` (no D-Bus secret service in the image).
  - `/defaults/autostart` — what openbox runs on session start; appends
    `$CLAUDE_DESKTOP_CLI`.
  - `/defaults/menu.xml` — right-click menu entry to relaunch the app.

`ENV PIXELFLUX_WAYLAND=false` pins the X11 path. The base image defaults to a
Wayland compositor, which mis-scales through the Olares entrance proxy.

## Build & push

```bash
# Single-arch (local dev)
docker build \
  --build-arg CLAUDE_DESKTOP_VERSION=1.28929.0 \
  -t ghcr.io/jasonlswenson-sys/claude-desktop-olares:1.28929.0-selkies1 .

# Multi-arch release (matches spec.supportArch: amd64, arm64)
docker buildx create --use --name claudedesktop-builder || true
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg CLAUDE_DESKTOP_VERSION=1.28929.0 \
  -t ghcr.io/jasonlswenson-sys/claude-desktop-olares:1.28929.0-selkies1 \
  --push .
```

Smoke test without Olares:

```bash
docker run --rm -p 3000:3000 --shm-size=1g \
  -v "$PWD/.tmp-config:/config" \
  ghcr.io/jasonlswenson-sys/claude-desktop-olares:1.28929.0-selkies1
# then open http://localhost:3000
```

## Bumping the app version

Anthropic publishes new `claude-desktop` versions to the apt repo continuously.
To find the newest one for an architecture:

```bash
curl -s "https://downloads.claude.ai/claude-desktop/apt/stable/dists/stable/main/binary-amd64/Packages" \
  | awk '/^Package: claude-desktop$/{p=1} p&&/^Version:/{print $2; p=0}' | sort -V | tail -1
```

Then, in one change:

1. `--build-arg CLAUDE_DESKTOP_VERSION=<new>` and rebuild/push with a new tag
   `<new>-selkies<n>`.
2. `appVersion` in `../Chart.yaml`.
3. `spec.versionName` in `../OlaresManifest.yaml`.
4. `image.tag` in `../values.yaml`.
5. `version` in `../Chart.yaml` and `metadata.version` in
   `../OlaresManifest.yaml` (chart version, bumped on every change).
6. `spec.upgradeDescription` in `../OlaresManifest.yaml` and both
   `../i18n/*/OlaresManifest.yaml`.

`../scripts/validate.py` checks 1–5 agree before you commit.

Bump only the `-selkies<n>` suffix when the change is to the base image or the
overlay and the app version is unchanged.
