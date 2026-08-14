# claudedesktop — Olares Market install package

An Olares Application Chart that installs **Claude Desktop for Linux** (Anthropic's
official `claude-desktop` package) into Olares and serves it as an app entrance
in the browser.

## Why it is packaged this way

Claude Desktop is a native Linux GUI application, not a web service. Olares apps
are reached over HTTP through an entrance, so the chart runs the app on a minimal
X11 desktop inside the container and streams that desktop to the browser with
Selkies — the same shape the official Olares `chromium` app uses. Opening the
entrance gives you the Claude window in a browser tab, from any device on your
Olares network.

The `claude-desktop` .deb comes from
[Anthropic's apt repository](https://code.claude.com/docs/en/desktop-linux) and
is baked into the image at build time with the signing key verified against its
published fingerprint. It installs to `/usr/lib` and `/usr/bin`, outside the
app's persistent volume, so installing at pod start would mean a root init
container repeating the work on every restart. Pinning at build time also makes
`Chart.appVersion` an exact statement of what a given image tag contains.

This is a *different* packaging format from the two sibling charts in
`infra/olares/` (`forms-engine`, `p6-ingest`). Those use an in-house
`app.olares.io/v1alpha1` manifest for internal host deployment. Olares Market
distribution requires the upstream Olares Application Chart format
(`olaresManifest.version: '0.12.0'`), which is what this package uses.

## Layout

| Path | Purpose |
| --- | --- |
| `Chart.yaml` | Helm chart metadata. `version` = packaging, `appVersion` = pinned `claude-desktop` version. |
| `OlaresManifest.yaml` | Market metadata, entrance, permissions, resource envelope, user-editable env vars. |
| `values.yaml` | Image reference, ports, `/dev/shm` size, resource requests/limits. |
| `templates/claudedesktop.yaml` | Deployment + Service. |
| `i18n/{en-US,zh-CN}/` | Localized title/description/full description. |
| `owners` | Market submission owners. |
| `docker/` | Image build inputs (Dockerfile + `/config` overlay). Excluded from the packaged chart. |
| `ci/olares-values.yaml` | Fixture standing in for Olares-injected values, for local `helm template`. Excluded. |
| `scripts/validate.py` | Structural + version-coherence checks. Excluded. |

## Configuration

Set from the app's environment variables in the Olares UI; all take effect on
restart (`applyOnChange: true`).

| Variable | Default | Effect |
| --- | --- | --- |
| `TZ` | `Etc/UTC` | Timezone of the streamed desktop. |
| `CLAUDE_DESKTOP_CLI` | *(empty)* | Extra flags appended to `claude-desktop`. The container's required flags are already applied by the launch wrapper. |
| `ALLOW_HOME_DIR_ACCESS` | `false` | Mounts the Olares Home drive at `/home/userdata/home`. |
| `ALLOW_EXTERNAL_DIR_ACCESS` | `false` | Mounts the Olares External drive at `/home/userdata/external`. |

Both file-access toggles default off, so out of the box the app can only see its
own private volume. Turn them on for Cowork and Code to work on real files.

The container home directory (`/config`) is backed by the app's private data
volume, so the signed-in session, settings, MCP server config, and Electron cache
survive restarts and upgrades.

On an **Olares One**, the chart detects `deviceName` and passes `/dev/dri`
through so the Electron compositor and the Selkies encoder use VA-API instead of
software rendering.

## Validate

```bash
python3 scripts/validate.py
```

Checks that the chart name, `appid`, and directory name agree; that every
required manifest field is present; that `Chart.appVersion`, `spec.versionName`,
`values.yaml` `image.tag`, and the Dockerfile's `CLAUDE_DESKTOP_VERSION` all name
the same upstream version; that each entrance host resolves to a Service the
templates define; and that the declared locales have parseable i18n files.

With Helm available, also render the templates:

```bash
helm lint .
helm template claudedesktop . -f ci/olares-values.yaml
```

## Build the image

See [`docker/README.md`](docker/README.md) for the build, push, and version-bump
procedure. The chart expects a multi-arch (`amd64`, `arm64`) image at the tag in
`values.yaml`.

## Install

**Sideload onto an Olares device** (no Market round trip):

```bash
olares-cli app install --path infra/olares/claudedesktop
```

**Submit to Olares Market:** fork [`beclab/apps`](https://github.com/beclab/apps),
copy this directory in as `claudedesktop/` at the repository root, and open a PR
against `beclab/apps:main`. Two prerequisites before submitting:

1. **Icon hosting.** `metadata.icon` and the entrance icon point at
   `https://app.cdn.olares.com/appstore/claudedesktop/icon.png`, the CDN path
   Olares serves accepted apps from. That object does not exist until the app is
   accepted — coordinate the icon upload with the Market maintainers, or point
   both fields at your own reachable HTTPS URL for the review.
2. **Public image.** `values.yaml` references
   `ghcr.io/jasonlswenson-sys/claude-desktop-olares`; it must be pullable
   anonymously for review installs to succeed.

Update `owners` to the GitHub handles that should be able to approve future
changes to the app.

## Known limitations

Inherited from the Linux desktop beta itself:

- **Computer Use** (screen and app control) is not available on Linux.
- **Voice dictation** is not available in the Linux desktop app.
- API-key auth is not accepted by the desktop app; sign in with a Claude account
  or organization SSO. For API-key workflows use the Claude Code CLI.

Specific to running it streamed in a container:

- The **Quick Entry global hotkey** is captured by the browser, not the streamed
  desktop.
- Audio is not wired through; the desktop streams video and input only.
- Electron runs with `--no-sandbox` because the pod has no user namespaces, and
  with `--password-store=basic` because the image has no D-Bus secret service.
  Isolation comes from the container and the Olares entrance auth instead of the
  Chromium sandbox; credentials sit in `$HOME` on the private volume rather than
  in a system keyring.
- The entrance is `private` (Olares SSO) by design — anyone who can open it is
  operating an already signed-in Claude session.
