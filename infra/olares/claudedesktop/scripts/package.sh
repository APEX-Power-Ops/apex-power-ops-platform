#!/usr/bin/env bash
# Package the chart into an archive that Olares Market's "Upload custom chart"
# accepts, so the app can be installed on a device without a Market submission.
#
# Uses `helm package` when helm is on PATH (canonical, honours .helmignore) and
# falls back to tar with the exclusions read out of .helmignore, so the two
# paths produce the same payload.
#
# Usage: scripts/package.sh [output-dir]     (default: <chart>/dist)

set -euo pipefail

CHART_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHART_NAME="$(basename "$CHART_DIR")"
PARENT_DIR="$(dirname "$CHART_DIR")"
OUT_DIR="${1:-$CHART_DIR/dist}"

# Fail before packaging rather than after uploading a chart that cannot install.
python3 "$CHART_DIR/scripts/validate.py" "$CHART_DIR"

VERSION="$(python3 -c "import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))['version'])" "$CHART_DIR/Chart.yaml")"
ARCHIVE="$OUT_DIR/$CHART_NAME-$VERSION.tgz"

mkdir -p "$OUT_DIR"
rm -f "$ARCHIVE"

if command -v helm > /dev/null 2>&1; then
  helm package "$CHART_DIR" --destination "$OUT_DIR" > /dev/null
else
  echo "helm not found; packaging with tar using .helmignore exclusions"
  excludes=()
  while IFS= read -r pattern; do
    case "$pattern" in
      ""|\#*) continue ;;
      # Directory patterns are chart-relative; anchor them so an unrelated
      # nested directory of the same name elsewhere is not silently dropped.
      */) excludes+=("--exclude=$CHART_NAME/${pattern%/}") ;;
      *)  excludes+=("--exclude=$pattern") ;;
    esac
  done < "$CHART_DIR/.helmignore"

  # Always keep the output directory out of its own archive.
  excludes+=("--exclude=$CHART_NAME/$(basename "$OUT_DIR")")

  tar -czf "$ARCHIVE" -C "$PARENT_DIR" "${excludes[@]}" "$CHART_NAME"
fi

echo
echo "Built $ARCHIVE"
echo "Contents:"
tar -tzf "$ARCHIVE" | sort | sed 's/^/  /'
echo
echo "Install: Olares Market > My Olares > Custom > Upload custom chart"
