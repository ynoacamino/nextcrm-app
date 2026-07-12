

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { load } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage, invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { idPool, pick, newAccountArgs, updateAccountArgs } from "../../lib/data.js";

const accounts = idPool("accounts");

export const options = {
  scenarios: { accounts_crud_load: load(10, 10) },
  thresholds: buildThresholds({ read: PRESETS.loadRead, write: PRESETS.loadWrite }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const read = { op: "read", suite: "PRLOAD", entity: "accounts" };
  const write = { op: "write", suite: "PRLOAD", entity: "accounts" };

  group("PRLOAD-018 creación de cuenta", () => {
    record(
      invokeServerAction("createAccount", ROUTES.accounts, newAccountArgs(), data.cookie, write),
      "write",
    );
  });

  const accountId = pick(accounts);
  if (accountId) {
    group("PRLOAD-019 actualización de cuenta", () => {
      record(
        invokeServerAction(
          "updateAccount",
          ROUTES.accounts,
          updateAccountArgs(accountId),
          data.cookie,
          write,
        ),
        "write",
      );
    });
    group("PRLOAD-022 página de detalle de cuenta", () => {
      record(readPage(ROUTES.accounts, data.cookie, read, `/${accountId}`), "read");
    });
  }

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRLOAD-accounts-crud");
