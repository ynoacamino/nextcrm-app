// PRSPIKE — Pico de tráfico sobre el listado de cuentas (lectura).
//
// META:
//   cases:    PRSPIKE-001, PRSPIKE-003, PRSPIKE-005, PRSPIKE-007
//   endpoint: GET /crm/accounts — getAccounts
//   objetivo: verificar ausencia de errores 5xx ante un pico repentino
//             (10 → 100 VU en 1 min), medir el p95 durante el pico, la tasa de
//             error de lectura y el tiempo de recuperación a p95 < 1s tras la caída.
//   umbral:   SPIKE — p95 < 2s, p99 < 3s, error < 2% (Diseño §4.3)
//   carga:    10 → 100 VU en 1 min, sostenido 5 min (Diseño §4.1 / Plan §5.1)

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { spike } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

export const options = {
  scenarios: { accounts_list_spike: spike(10, 100, 5) },
  thresholds: buildThresholds({ read: PRESETS.spike }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "read", suite: "PRSPIKE", entity: "accounts" };
  group("PRSPIKE-001/005/007 listado de cuentas durante pico", () => {
    record(readPage(ROUTES.accounts, data.cookie, t, "?page=1"), "read");
  });
  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSPIKE-accounts-list");
