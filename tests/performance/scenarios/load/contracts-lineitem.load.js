

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { load } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { idPool, pick, newLineItemArgs } from "../../lib/data.js";

const contracts = idPool("contracts");

export const options = {
  scenarios: { contracts_lineitem_load: load(20, 10) },
  thresholds: buildThresholds({ write: PRESETS.loadWrite }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "write", suite: "PRLOAD", entity: "contracts" };
  const contractId = pick(contracts);
  if (!contractId) {
    sleep(1);
    return;
  }

  group("PRLOAD-021 adición de partida a contrato", () => {
    record(
      invokeServerAction(
        "addContractLineItem",
        ROUTES.contracts,
        newLineItemArgs(contractId),
        data.cookie,
        t,
      ),
      "write",
    );
  });

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRLOAD-contracts-lineitem");
