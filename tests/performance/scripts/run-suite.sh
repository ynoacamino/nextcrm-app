#!/usr/bin/env bash

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS="${REPORTS_DIR:-$HERE/reports}"
SUITE="${1:?Uso: $0 <suite> [extra-k6-args...]}"
shift

EXTRA_ARGS=("$@")

mkdir -p "$REPORTS"

k6_run() {
  local f="$1"
  local name
  name="$(basename "$f" | sed 's/\.[^.]*$//')"
  echo "════════════════════════════════════════════════════════════"
  echo "▶ k6 run $(basename "$f")"
  echo "════════════════════════════════════════════════════════════"
  ( cd "$HERE" && k6 run --summary-export="$REPORTS/$name.json" --out csv="$REPORTS/$name-raw-metrics.csv" "${EXTRA_ARGS[@]}" "$f" )
}

case "$SUITE" in
  smoke)
    export DURATION_SCALE="${DURATION_SCALE:-0.05}"
    for f in "$HERE"/scenarios/load/*.load.js; do k6_run "$f" || true; done
    ;;
  load|stress|spike|soak)
    for f in "$HERE"/scenarios/"$SUITE"/*."$SUITE".js; do k6_run "$f" || true; done
    ;;
  *)
    echo "Suite desconocida: $SUITE (usa load|stress|spike|soak|smoke)" >&2
    exit 1
    ;;
esac
