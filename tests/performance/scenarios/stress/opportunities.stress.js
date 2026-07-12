

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { stress } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage, invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { idPool, pick, newOpportunityArgs } from "../../lib/data.js";

const accounts = idPool("accounts");

export const options = {
  scenarios: { opportunities_stress: stress(5, 20, 15) },
  thresholds: buildThresholds({ read: PRESETS.stressRead, write: PRESETS.stressWrite }),
};

export function setup() {
  const cookie = authenticate();
  return { cookie };
}

export default function (data) {
  const read = { op: "read", suite: "PRSTRESS", entity: "opportunities" };
  const write = { op: "write", suite: "PRSTRESS", entity: "opportunities" };

  group("PRSTRESS-004 listado de oportunidades bajo saturación", () => {
    record(readPage(ROUTES.opportunities, data.cookie, read, "?stage=PROPOSAL"), "read");
  });

  group("PRSTRESS-010 creación de oportunidad (degradación)", () => {
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

  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSTRESS-opportunities");
