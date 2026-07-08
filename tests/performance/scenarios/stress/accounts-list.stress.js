// PRSTRESS — Saturación del listado de cuentas (lectura bajo carga creciente).
//
// META:
//   cases:    PRSTRESS-001, PRSTRESS-007, PRSTRESS-009, PRSTRESS-014, PRSTRESS-015
//   endpoint: GET /crm/accounts — getAccounts
//   objetivo: localizar el punto de saturación (10 → 200+ VU), medir la tasa de
//             error y la degradación del tiempo de respuesta durante la rampa,
//             identificar el cuello de botella principal y verificar la
//             recuperación tras la caída de carga.
//   umbral:   lectura STRESS — p95 < 2s, p99 < 3s, error < 2% (Diseño §4.3)
//   carga:    rampa 10 → 200 VU, 20 min (Diseño §4.1)
//   nota:     PRSTRESS-014 (cuello de botella) y PRSTRESS-011/012/013 (recursos)
//             se analizan correlacionando esta ejecución con Prometheus/Grafana.

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { stress } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

export const options = {
  scenarios: { accounts_list_stress: stress(10, 200, 20) },
  thresholds: buildThresholds({ read: PRESETS.stressRead }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "read", suite: "PRSTRESS", entity: "accounts" };

  group("PRSTRESS-001/007/009 listado bajo saturación", () => {
    record(readPage(ROUTES.accounts, data.cookie, t, "?page=1&sort=name"), "read");
  });

  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSTRESS-accounts-list");
