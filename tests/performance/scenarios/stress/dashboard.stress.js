// PRSTRESS — Saturación del dashboard (lectura compleja).
//
// META:
//   cases:    PRSTRESS-005
//   endpoint: GET /crm/dashboard — resúmenes agregados
//   objetivo: punto de saturación del dashboard (10 → 100 VU); es la operación
//             de lectura más costosa por agregar múltiples consultas.
//   umbral:   compleja STRESS — p95 < 4s, p99 < 6s, error < 2% (Diseño §4.3)
//   carga:    rampa 10 → 100 VU, 15 min

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { stress } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

export const options = {
  scenarios: { dashboard_stress: stress(10, 100, 15) },
  thresholds: buildThresholds({ complex: PRESETS.stressComplex }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "complex", suite: "PRSTRESS", entity: "dashboard" };
  group("PRSTRESS-005 dashboard bajo saturación", () => {
    record(readPage(ROUTES.dashboard, data.cookie, t), "complex");
  });
  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSTRESS-dashboard");
