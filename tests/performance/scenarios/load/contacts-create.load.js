

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { load } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { newContactArgs } from "../../lib/data.js";

export const options = {
  scenarios: { contacts_create_load: load(20, 10) },
  thresholds: buildThresholds({ write: PRESETS.loadWrite }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "write", suite: "PRLOAD", entity: "contacts" };

  group("PRLOAD-006/007/008 creación de contacto", () => {
    const res = invokeServerAction(
      "createContact",
      ROUTES.contacts,
      newContactArgs(),
      data.cookie,
      t,
    );
    record(res, "write");
  });

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRLOAD-contacts-create");
