

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { soak } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

const HOURS = Number(__ENV.SOAK_HOURS || 4);
const VUS = Number(__ENV.SOAK_VUS || 8);

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
