

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { load } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage, invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { idPool, pick, updateOpportunityArgs } from "../../lib/data.js";

const opportunities = idPool("opportunities");

export const options = {
  scenarios: { opportunities_load: load(12, 10) },
  thresholds: buildThresholds({ read: PRESETS.loadRead, write: PRESETS.loadWrite }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const read = { op: "read", suite: "PRLOAD", entity: "opportunities" };
  const write = { op: "write", suite: "PRLOAD", entity: "opportunities" };

  group("PRLOAD-017 listado de oportunidades por etapa", () => {
    record(readPage(ROUTES.opportunities, data.cookie, read, "?stage=PROPOSAL"), "read");
  });

  const oppId = pick(opportunities);
  if (oppId) {
    group("PRLOAD-011 actualización de oportunidad", () => {
      const res = invokeServerAction(
        "updateOpportunity",
        ROUTES.opportunities,
        updateOpportunityArgs(oppId),
        data.cookie,
        write,
      );
      record(res, "write");
    });
  }

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRLOAD-opportunities");
