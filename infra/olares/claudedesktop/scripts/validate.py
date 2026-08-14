#!/usr/bin/env python3
"""Structural checks for the claudedesktop Olares Application Chart.

Catches the mistakes that only surface after a Market submission is rejected or
after an install renders a broken entrance: version fields drifting apart across
Chart.yaml / OlaresManifest.yaml / values.yaml / Dockerfile, a required manifest
field going missing, an entrance pointing at a Service name that no template
defines, or an i18n override that no longer parses.

This does not render the Helm templates. Run
`helm lint . && helm template claudedesktop . -f ci/olares-values.yaml`
for that when helm is available.

Usage: python3 scripts/validate.py [chart-dir]   (default: script's parent dir)
Exit code 0 = all checks passed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REQUIRED_METADATA = ("name", "description", "icon", "appid", "version", "title", "categories")
REQUIRED_SPEC = (
    "versionName",
    "fullDescription",
    "developer",
    "website",
    "submitter",
    "doc",
    "license",
    "requiredMemory",
    "limitedMemory",
    "requiredDisk",
    "limitedDisk",
    "requiredCpu",
    "limitedCpu",
    "supportArch",
)
REQUIRED_ENTRANCE = ("name", "host", "port", "title")
SUPPORTED_ARCH = {"amd64", "arm64"}
APPID_RE = re.compile(r"^[a-z][a-z0-9]{2,29}$")


class Failures(list):
    def check(self, ok: bool, message: str) -> bool:
        if not ok:
            self.append(message)
        return ok


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def service_names(templates_dir: Path) -> set[str]:
    """Names of Services declared in the templates.

    Templates are Helm sources, so they are not valid YAML. The Service names
    this chart cares about are literals, so scan the docs textually and take the
    first `name:` after a `kind: Service`.
    """
    names: set[str] = set()
    for template in sorted(templates_dir.glob("*.yaml")):
        for doc in template.read_text(encoding="utf-8").split("\n---"):
            if not re.search(r"^\s*kind:\s*Service\s*$", doc, re.MULTILINE):
                continue
            match = re.search(r"^\s{2}name:\s*(\S+)\s*$", doc, re.MULTILINE)
            if match:
                names.add(match.group(1).strip("\"'"))
    return names


def main(chart_dir: Path) -> int:
    f = Failures()

    chart = load(chart_dir / "Chart.yaml")
    manifest = load(chart_dir / "OlaresManifest.yaml")
    values = load(chart_dir / "values.yaml")
    dockerfile = (chart_dir / "docker" / "Dockerfile").read_text(encoding="utf-8")

    metadata = manifest.get("metadata") or {}
    spec = manifest.get("spec") or {}
    entrances = manifest.get("entrances") or []

    # --- identity -----------------------------------------------------------
    appid = metadata.get("appid")
    f.check(
        chart.get("name") == appid,
        f"Chart.yaml name {chart.get('name')!r} != metadata.appid {appid!r}",
    )
    f.check(
        metadata.get("name") == appid,
        f"metadata.name {metadata.get('name')!r} != metadata.appid {appid!r}",
    )
    f.check(
        chart_dir.name == appid,
        f"chart directory {chart_dir.name!r} != metadata.appid {appid!r}",
    )
    f.check(
        bool(appid and APPID_RE.match(appid)),
        f"metadata.appid {appid!r} must be 3-30 lowercase letters/digits starting with a letter",
    )

    # --- required fields ----------------------------------------------------
    for key in REQUIRED_METADATA:
        f.check(metadata.get(key) not in (None, "", []), f"metadata.{key} is missing or empty")
    for key in REQUIRED_SPEC:
        f.check(spec.get(key) not in (None, "", []), f"spec.{key} is missing or empty")
    f.check(bool(manifest.get("olaresManifest.version")), "olaresManifest.version is missing")
    f.check(manifest.get("olaresManifest.type") == "app", "olaresManifest.type must be 'app'")

    arch = set(spec.get("supportArch") or [])
    f.check(
        bool(arch) and arch <= SUPPORTED_ARCH,
        f"spec.supportArch {sorted(arch)} must be a non-empty subset of {sorted(SUPPORTED_ARCH)}",
    )

    # --- version coherence --------------------------------------------------
    # Chart version tracks the packaging; appVersion tracks the upstream .deb.
    f.check(
        str(chart.get("version")) == str(metadata.get("version")),
        f"Chart.yaml version {chart.get('version')!r} != metadata.version {metadata.get('version')!r}",
    )
    app_version = str(chart.get("appVersion"))
    f.check(
        app_version == str(spec.get("versionName")),
        f"Chart.yaml appVersion {app_version!r} != spec.versionName {spec.get('versionName')!r}",
    )

    image_tag = str((values.get("image") or {}).get("tag", ""))
    f.check(
        image_tag.startswith(f"{app_version}-"),
        f"values.yaml image.tag {image_tag!r} does not start with appVersion {app_version!r}",
    )

    arg = re.search(r"^ARG\s+CLAUDE_DESKTOP_VERSION=(\S+)\s*$", dockerfile, re.MULTILINE)
    if f.check(arg is not None, "docker/Dockerfile has no ARG CLAUDE_DESKTOP_VERSION default"):
        f.check(
            arg.group(1) == app_version,
            f"Dockerfile CLAUDE_DESKTOP_VERSION {arg.group(1)!r} != Chart.yaml appVersion {app_version!r}",
        )

    # --- entrances ----------------------------------------------------------
    services = service_names(chart_dir / "templates")
    f.check(bool(entrances), "no entrances declared")
    for entrance in entrances:
        for key in REQUIRED_ENTRANCE:
            f.check(entrance.get(key) not in (None, ""), f"entrance {entrance.get('name')!r}: {key} is missing")
        host = entrance.get("host")
        f.check(
            host in services,
            f"entrance host {host!r} has no matching Service in templates/ (found: {sorted(services)})",
        )

    # --- workload replicas --------------------------------------------------
    for workload in (manifest.get("workloadReplicas") or {}):
        f.check(
            workload in (values.get("workloads") or {}),
            f"workloadReplicas.{workload} has no matching values.yaml workloads.{workload}",
        )

    # --- i18n ---------------------------------------------------------------
    for locale in spec.get("locale") or []:
        path = chart_dir / "i18n" / locale / "OlaresManifest.yaml"
        if not f.check(path.is_file(), f"spec.locale lists {locale!r} but {path.relative_to(chart_dir)} is missing"):
            continue
        translated = load(path) or {}
        f.check(
            bool((translated.get("metadata") or {}).get("title")),
            f"{locale}: metadata.title is missing",
        )
        f.check(
            bool((translated.get("spec") or {}).get("fullDescription")),
            f"{locale}: spec.fullDescription is missing",
        )

    # --- packaging ----------------------------------------------------------
    for required_file in ("owners", ".helmignore", "values.yaml", "README.md"):
        f.check((chart_dir / required_file).is_file(), f"{required_file} is missing")

    helmignore = (chart_dir / ".helmignore").read_text(encoding="utf-8").splitlines()
    for build_only in ("docker/", "ci/", "scripts/", "dist/"):
        f.check(build_only in helmignore, f".helmignore does not exclude build-only directory {build_only!r}")

    if f:
        print(f"FAIL: {len(f)} problem(s) in {chart_dir}", file=sys.stderr)
        for message in f:
            print(f"  - {message}", file=sys.stderr)
        return 1

    print(f"OK: {chart_dir.name} chart {chart.get('version')} (claude-desktop {app_version})")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    raise SystemExit(main(target.resolve()))
