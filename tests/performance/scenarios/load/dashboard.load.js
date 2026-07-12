

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { load } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

export const options = {
  scenarios: { dashboard_load: load(10, 10) },
  thresholds: buildThresholds({ complex: PRESETS.loadComplex }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "complex", suite: "PRLOAD", entity: "dashboard" };

  group("PRLOAD-012 dashboard con resúmenes", () => {
    record(readPage(ROUTES.dashboard, data.cookie, t), "complex");
  });

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRLOAD-dashboard");
