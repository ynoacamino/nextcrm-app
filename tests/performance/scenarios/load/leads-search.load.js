

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { load } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

export const options = {
  scenarios: { leads_search_load: load(15, 10) },
  thresholds: buildThresholds({ read: PRESETS.loadRead }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "read", suite: "PRLOAD", entity: "leads" };

  group("PRLOAD-015 búsqueda por nombre", () => {
    record(readPage(ROUTES.leads, data.cookie, t, "?q=Perf&field=name"), "read");
  });
  group("PRLOAD-016 búsqueda por email", () => {
    record(readPage(ROUTES.leads, data.cookie, t, "?q=perf.test&field=email"), "read");
  });

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRLOAD-leads-search");
