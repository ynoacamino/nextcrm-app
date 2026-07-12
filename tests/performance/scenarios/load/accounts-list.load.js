

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { load } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

export const options = {
  scenarios: { accounts_list_load: load(15, 10) },
  thresholds: buildThresholds({ read: PRESETS.loadRead }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "read", suite: "PRLOAD", entity: "accounts" };

  group("PRLOAD-001/002/003 listado paginado", () => {
    record(readPage(ROUTES.accounts, data.cookie, t), "read");
  });
  group("PRLOAD-025 paginación (página 2)", () => {
    record(readPage(ROUTES.accounts, data.cookie, t, "?page=2"), "read");
  });
  group("PRLOAD-023 ordenación por nombre", () => {
    record(readPage(ROUTES.accounts, data.cookie, t, "?sort=name&order=asc"), "read");
  });
  group("PRLOAD-024 ordenación por fecha de creación", () => {
    record(readPage(ROUTES.accounts, data.cookie, t, "?sort=createdAt&order=desc"), "read");
  });

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRLOAD-accounts-list");
