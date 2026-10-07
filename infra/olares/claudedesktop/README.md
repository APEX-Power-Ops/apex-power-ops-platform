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
| `scripts/package.sh` | Builds the uploadable chart archive into `dist/`. Excluded. |

## Getting your repo into the app

An Olares app is sandboxed. It cannot see a checkout on your laptop, and it
cannot see this repository's working copy on the machine you ran `package.sh`
from — installing the chart ships the *packaging*, not the code. Three ways to
close that gap, and the first is almost always the right one.

### The shared `Home/Code` workspace (default, nothing to enable)

The chart mounts the `Code` folder of your Olares Home drive at `~/workspace`
inside the container. This is the same directory the official
[code-server](https://market.olares.com/app/codeserver) and
[opencode](https://market.olares.com/app/opencode) apps mount, so it is the
established place for source on an Olares device.

Clone once from the app's own terminal:

```bash
cd ~/workspace
git clone https://github.com/APEX-Power-Ops/apex-power-ops-platform.git
```

Every app that mounts `Home/Code` then sees the same working tree, and the Files
app can browse it. `git`, `openssh-client`, `gcc`/`g++`/`make`/`cmake`, and
`python3` all ship in the base image, so cloning, building, and pushing work
without adding anything.

Git is the sync boundary between the Olares desktop and your workstation: both
push to and pull from GitHub. Do not expect a live mirror of a laptop directory
— nothing in Olares provides that.

Two apps writing the same worktree at the same time will fight over the index
and over `.git/` locks. If you also run Claude Code or code-server against this
directory, work in one at a time, or give each its own clone.

### The whole Home drive (`ALLOW_HOME_DIR_ACCESS`)

Mounts the entire Home drive at `/home/userdata/home`. Only needed to reach
documents, photos, or other non-code folders — the workspace above needs no
toggle. Default off.

### The External drive (`ALLOW_EXTERNAL_DIR_ACCESS`)

Mounts attached storage at `/home/userdata/external`, for large trees or media
that do not belong on Home. Default off.

### A note on storage tiers

Olares exposes three tiers, and they behave differently under a cluster with
JuiceFS enabled ([data
concepts](https://docs.olares.com/manual/concepts/data.html)):

- **AppData** — cross-node, JuiceFS-backed, included in system backups. `/config`
  lives here, matching what the official `chromium` app does (it deliberately
  migrated its profile from AppCache to AppData).
- **AppCache** — node-local SSD, fast, not cross-node.
- **UserData** — the Home drive, shared across apps. `~/workspace` lives here.

On a default single-node install with no JuiceFS these are all local disk and
the distinction does not bite. On a JuiceFS-backed cluster, an Electron profile
and a git worktree are both fragmented random I/O, which is the workload JuiceFS
is worst at. If the desktop feels sluggish there, move `/config` to
`.Values.userspace.appCache` — at the cost of pinning the pod to one node and
dropping the profile out of system backups.

## Configuration

Set from the app's environment variables in the Olares UI; all take effect on
restart (`applyOnChange: true`).

| Variable | Default | Effect |
| --- | --- | --- |
| `TZ` | `Etc/UTC` | Timezone of the streamed desktop. |
| `CLAUDE_DESKTOP_CLI` | *(empty)* | Extra flags appended to `claude-desktop`. The container's required flags are already applied by the launch wrapper. |
| `ALLOW_HOME_DIR_ACCESS` | `false` | Mounts the **whole** Home drive at `/home/userdata/home`. Not needed for code — see the workspace above. |
| `ALLOW_EXTERNAL_DIR_ACCESS` | `false` | Mounts the Olares External drive at `/home/userdata/external`. |

The container home directory (`/config`) is backed by the app's private data
volume, so the signed-in session, settings, MCP server config, and Electron cache
survive restarts and upgrades. `~/workspace` is the exception: it is the shared
`Home/Code` directory, mounted unconditionally.

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

## Install without Olares Market

Market submission is optional. Olares installs an Application Chart from an
uploaded archive, so this package can run on a device that never sees the public
Market. Three routes, in order of how most people should reach for them.

Note that `olares-cli` is **not** one of them: it manages the Olares OS itself
(`install`, `start`, `stop`, `backups`, `node`, `gpu`), and has no app-install
subcommand.

### 1. Upload a custom chart (recommended)

Build the archive, then upload it through the Market UI:

```bash
scripts/package.sh          # writes dist/claudedesktop-<version>.tgz
```

Then in Olares: **Market** → **My Olares** → **Custom** → **Upload custom
chart**, and select the `.tgz`. Olares accepts `.zip`, `.tgz`, `.tar`, and `.gz`;
the archive must contain the chart directory at its root, which is what
`package.sh` produces. It installs, upgrades, and uninstalls exactly like a
Market app, and appears under **Custom** rather than in the public listing.

`package.sh` runs `validate.py` first and excludes the build-only directories
per `.helmignore`, so `docker/`, `ci/`, `scripts/`, and `dist/` stay out of the
payload. It uses `helm package` when helm is on PATH and falls back to `tar`
with the same exclusions otherwise.

This route drops the icon constraint that a Market submission carries: point
`metadata.icon` and the entrance icon at any HTTPS URL your device can reach.

### 2. DevBox, for iterating against a live device

[DevBox](https://market.olares.com/app/devbox) is Olares' app development tool.
It gives you an editable copy of the chart files, an **Install** button that
deploys the in-progress app onto the system, and a chart download once it works.
Reach for it when you are changing the manifest or templates and want a short
edit-install-inspect loop instead of rebuilding an archive each time.

### 3. `InstallDevApp` provider API, for automation

The Market exposes `InstallDevApp` / `UninstallDevApp` for programmatic installs
— this is what DevBox itself calls:

```
POST http://$OS_SYSTEM_SERVER/system-server/v1alpha1/app/service.appstore/v1/InstallDevApp
{"appName": "claudedesktop", "repoUrl": "<chart repo URL>", "source": "<source>"}
```

The caller must be an installed Olares app that declares the provider in its
manifest, and must exchange its `OS_APP_KEY` / `OS_APP_SECRET` for a
short-lived access token first:

```yaml
permission:
  sysData:
  - group: service.appstore
    dataType: app
    version: v1
    ops:
    - InstallDevApp
```

That makes it the right route only for an installer app or a CI agent already
running inside Olares — not for a one-off install from a laptop.

## Submit to Olares Market

Fork [`beclab/apps`](https://github.com/beclab/apps), copy this directory in as
`claudedesktop/` at the repository root, and open a **draft** PR against
`beclab/apps:main` titled `[NEW][claudedesktop][0.1.0]<title>` — GitBot parses
that format and auto-closes PRs that do not match. Mark it ready for review to
trigger the check.

Two prerequisites beyond the packaging itself:

1. **Icon hosting.** `metadata.icon` and the entrance icon point at
   `https://app.cdn.olares.com/appstore/claudedesktop/icon.png`, the CDN path
   Olares serves accepted apps from. That object does not exist until the app is
   accepted — coordinate the icon upload with the Market maintainers, or point
   both fields at your own reachable HTTPS URL for the review. Market assets must
   be PNG or WEBP, 256x256 px, up to 512 KB.
2. **Public image.** `values.yaml` references
   `ghcr.io/jasonlswenson-sys/claude-desktop-olares`; it must be pullable
   anonymously for review installs to succeed.

Update `owners` to the GitHub handles that should be able to approve future
changes to the app — every submitter must appear in that file.

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
