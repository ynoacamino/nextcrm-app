// PRSOAK — Resistencia con CRUD mixto (detección de fugas de memoria/recursos).
//
// META:
//   cases:    PRSOAK-003, PRSOAK-004, PRSOAK-005, PRSOAK-009
//   endpoint: mezcla de lecturas (accounts/dashboard) y escrituras (createContact)
//   objetivo: mantener un flujo CRUD constante para detectar fugas de memoria del
//             proceso Next.js (003) y de PostgreSQL (004), estabilidad de las
//             conexiones a PostgreSQL (005) y de la memoria de las herramientas
//             de monitoreo (009).
//   umbral:   SOAK — p95 < 1s, p99 < 1.5s, error < 0.5% (Diseño §4.3)
//   carga:    20 VU, 8 h (Plan §5.1 SOAK-02). Acortar con -e DURATION_SCALE.
//   nota:     003/004/005/009 se evalúan observando en Grafana la tendencia de
//             memoria (RSS del proceso Node y de PostgreSQL) y el número de
//             conexiones activas durante toda la ventana; deben permanecer planos.

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { soak } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage, invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { newContactArgs } from "../../lib/data.js";

const HOURS = Number(__ENV.SOAK_HOURS || 8);
const VUS = Number(__ENV.SOAK_VUS || 20);

export const options = {
  scenarios: { mixed_crud_soak: soak(VUS, HOURS) },
  thresholds: buildThresholds({ read: PRESETS.soak, write: PRESETS.soak }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const read = { op: "read", suite: "PRSOAK", entity: "mixed" };
  const write = { op: "write", suite: "PRSOAK", entity: "mixed" };

  group("PRSOAK-003/004/005 lectura sostenida (accounts)", () => {
    record(readPage(ROUTES.accounts, data.cookie, read, "?page=1"), "read");
  });
  group("PRSOAK-003/004/005 lectura agregada (dashboard)", () => {
    record(readPage(ROUTES.dashboard, data.cookie, read), "read");
  });
  group("PRSOAK-003/004/005 escritura sostenida (createContact)", () => {
    record(
      invokeServerAction("createContact", ROUTES.contacts, newContactArgs(), data.cookie, write),
      "write",
    );
  });

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRSOAK-mixed-crud");
