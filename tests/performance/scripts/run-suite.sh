#!/usr/bin/env bash

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS="${REPORTS_DIR:-$HERE/reports}"
SUITE="${1:-load}"
shift || true

mkdir -p "$REPORTS"

PASSED=0
FAILED=0
FAILED_TESTS=""

k6_run() {
  local f="$1"
  local name
  name="$(basename "$f" | sed 's/\.[^.]*$//')"
  shift
  echo "════════════════════════════════════════════════════════════"
  echo "▶ k6 run $(basename "$f")"
  echo "════════════════════════════════════════════════════════════"
  if ( cd "$HERE" && k6 run --summary-export="$REPORTS/$name.json" --out csv="$REPORTS/$name-raw-metrics.csv" "$@" "$f" ); then
    PASSED=$((PASSED + 1))
    echo "✅ $(basename "$f") completado exitosamente"
  else
    FAILED=$((FAILED + 1))
    FAILED_TESTS="$FAILED_TESTS  - $(basename "$f")\n"
    echo "❌ $(basename "$f") falló (exit $?), continuando con el siguiente..."
  fi
  echo ""
}

run_suite() {
  local suite="$1"
  local count=0
  for f in "$HERE"/scenarios/"$suite"/*."$suite".js; do
    [ -f "$f" ] || continue
    count=$((count + 1))
    k6_run "$f" "$@"
  done
  return $count
}

case "$SUITE" in
  smoke)
    export DURATION_SCALE="${DURATION_SCALE:-0.05}"
    echo "▶ Ejecutando suite SMOKE (DURATION_SCALE=$DURATION_SCALE)"
    for f in "$HERE"/scenarios/load/*.load.js; do
      [ -f "$f" ] || continue
      k6_run "$f" "$@"
    done
    ;;
  load|stress|spike|soak)
    echo "▶ Ejecutando suite ${SUITE^^}"
    run_suite "$SUITE" "$@"
    ;;
  all)
    echo "▶ Ejecutando TODAS las suites"
    export DURATION_SCALE="${DURATION_SCALE:-0.05}"
    for s in smoke load stress spike soak; do
      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "▶ Suite: $s"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      if [ "$s" = "smoke" ]; then
        for f in "$HERE"/scenarios/load/*.load.js; do
          [ -f "$f" ] || continue
          k6_run "$f" "$@"
        done
      else
        run_suite "$s" "$@"
      fi
    done
    ;;
  *)
    echo "Suite desconocida: $SUITE (usa load|stress|spike|soak|smoke|all)" >&2
    exit 1
    ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "▶ RESUMEN: $PASSED pasaron, $FAILED fallaron"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$FAILED" -gt 0 ]; then
  echo -e "Tests que fallaron:\n$FAILED_TESTS"
fi
echo ""
ls -la "$REPORTS"/*.json 2>/dev/null || echo "No hay reportes JSON generados"
