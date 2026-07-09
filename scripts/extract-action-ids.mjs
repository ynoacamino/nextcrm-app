import { readFileSync } from "node:fs";
const m = JSON.parse(readFileSync("./.next/server/server-reference-manifest.json", "utf8"));
const node = m.node;
const want = [
  "createContact", "deleteContact", "createAccount", "updateAccount",
  "createOpportunity", "updateOpportunity", "createActivity", "convertTarget",
  "addContractLineItem",
];
const found = {};
for (const [hash, entry] of Object.entries(node)) {
  for (const w of Object.values(entry.workers || {})) {
    if (want.includes(w.exportedName) && !found[w.exportedName]) found[w.exportedName] = hash;
    if (w.filename && w.filename.includes("add-line-item") && !found.addContractLineItem)
      found.addContractLineItem = hash;
  }
}
const lines = [];
for (const k of want) {
  console.log(k, found[k] || "NOT FOUND");
  if (found[k]) lines.push(`AID_${k}=${found[k]}`);
}
writeEnv(lines);
function writeEnv(lines) {
  import("node:fs").then((fs) =>
    fs.writeFileSync("scripts/.aids.env", lines.join("\n") + "\n"),
  );
}
