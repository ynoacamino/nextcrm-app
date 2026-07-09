

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
