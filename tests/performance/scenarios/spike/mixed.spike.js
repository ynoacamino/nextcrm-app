// PRSPIKE — Pico combinado lectura + escritura.
//
// META:
//   cases:    PRSPIKE-004, PRSPIKE-006
//   endpoint: GET /crm/accounts (lectura) + Server Action createOpportunity (escritura)
//   objetivo: manejo de un pico combinado de lectura y escritura (10 → 150 VU) y
//             medición del p95 de creación de oportunidades durante el pico.
//   umbral:   SPIKE — p95 < 2s, p99 < 3s, error < 2% (Diseño §4.3)
//   carga:    10 → 150 VU en 1 min, sostenido 3 min (Plan §5.1 SPIKE-02)
//   requiere: pool de accounts en data/entity-ids.json (clave "accounts").
//
// Reparto de tráfico: ~70% lecturas / ~30% escrituras, para reproducir un
// pico realista dominado por navegación con creaciones intercaladas.

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { spike } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage, invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { idPool, pick, newOpportunityArgs } from "../../lib/data.js";

const accounts = idPool("accounts");

export const options = {
  scenarios: { mixed_spike: spike(10, 150, 3) },
  thresholds: buildThresholds({ read: PRESETS.spike, write: PRESETS.spike }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const read = { op: "read", suite: "PRSPIKE", entity: "accounts" };
  const write = { op: "write", suite: "PRSPIKE", entity: "opportunities" };

  if (Math.random() < 0.7) {
    group("PRSPIKE-004 lectura durante pico combinado", () => {
      record(readPage(ROUTES.accounts, data.cookie, read), "read");
    });
  } else {
    group("PRSPIKE-006 creación de oportunidad durante pico", () => {
      const accountId = pick(accounts);
      record(
        invokeServerAction(
          "createOpportunity",
          ROUTES.opportunities,
          newOpportunityArgs(accountId),
          data.cookie,
          write,
        ),
        "write",
      );
    });
  }

  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSPIKE-mixed");
