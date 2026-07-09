#!/usr/bin/env bash
# Ejecuta una familia de escenarios de rendimiento en el orden del Diseño §4.1
# (LOAD -> STRESS -> SPIKE -> SOAK). No paraleliza suites sobre el mismo entorno
# (Diseño §3.4.3).
#
# Uso:
#   tests/performance/scripts/run-suite.sh load      # todos los LOAD
#   tests/performance/scripts/run-suite.sh stress
#   tests/performance/scripts/run-suite.sh spike
#   tests/performance/scripts/run-suite.sh soak
#   tests/performance/scripts/run-suite.sh smoke     # humo rápido (DURATION_SCALE=0.05)
#
# Variables útiles (se pasan a k6):
#   BASE_URL, LOCALE, ADMIN_EMAIL, SESSION_COOKIE, DURATION_SCALE, TARGET_RPS,
#   AID_<accion> (Next-Action IDs). Ver README.md.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUITE="${1:-load}"
shift || true

k6_run() {
  local f="$1"
  shift
  echo "════════════════════════════════════════════════════════════"
  echo "▶ k6 run $(basename "$f")"
  echo "════════════════════════════════════════════════════════════"
  ( cd "$HERE" && k6 run "$@" "$f" )
}

case "$SUITE" in
  smoke)
    export DURATION_SCALE="${DURATION_SCALE:-0.05}"
    for f in "$HERE"/scenarios/load/*.load.js; do k6_run "$f" "$@"; done
    ;;
  load|stress|spike|soak)
    for f in "$HERE"/scenarios/"$SUITE"/*."$SUITE".js; do k6_run "$f" "$@"; done
    ;;
  *)
    echo "Suite desconocida: $SUITE (usa load|stress|spike|soak|smoke)" >&2
    exit 1
    ;;
esac
