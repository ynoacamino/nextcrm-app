// PRSOAK — Resistencia del listado de cuentas (lectura sostenida).
//
// META:
//   cases:    PRSOAK-001, PRSOAK-006, PRSOAK-007, PRSOAK-008
//   endpoint: GET /crm/accounts — getAccounts
//   objetivo: bajo carga sostenida (30 VU, 4 h; o 20 VU, 8 h con -e SOAK_HOURS=8)
//             verificar degradación < 10% en tiempo de respuesta y throughput,
//             ausencia de errores de timeout y de errores de conexión a BD.
//   umbral:   SOAK — p95 < 1s, p99 < 1.5s, error < 0.5% (Diseño §4.3)
//   carga:    30 VU, 4 h (Diseño §4.1). Acortar con -e DURATION_SCALE.
//   nota:     comparar el p95 del primer y último tercio de la ejecución en
//             Grafana para cuantificar la degradación (< 10%).

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { soak } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

const HOURS = Number(__ENV.SOAK_HOURS || 4);
const VUS = Number(__ENV.SOAK_VUS || 30);

export const options = {
  scenarios: { accounts_list_soak: soak(VUS, HOURS) },
  thresholds: buildThresholds({ read: PRESETS.soak }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "read", suite: "PRSOAK", entity: "accounts" };
  group("PRSOAK-001/006/007/008 listado de cuentas sostenido", () => {
    record(readPage(ROUTES.accounts, data.cookie, t, "?page=1&sort=name"), "read");
  });
  sleep(1);
}

export const handleSummary = makeHandleSummary("PRSOAK-accounts-list");
