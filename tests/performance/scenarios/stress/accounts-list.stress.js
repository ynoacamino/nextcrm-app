

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
