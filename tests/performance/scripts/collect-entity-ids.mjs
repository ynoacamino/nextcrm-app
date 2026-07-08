// Recolecta IDs de entidades sembradas y los vuelca en data/entity-ids.json.
//
// Los escenarios de k6 que operan sobre entidades existentes (update, convert,
// line-item, actividades por entidad) leen ese pool con lib/data.js#idPool.
//
// Uso:
//   node tests/performance/scripts/collect-entity-ids.mjs
//   POOL_SIZE=500 DATABASE_URL=postgres://... node tests/performance/scripts/collect-entity-ids.mjs
//
// Requisitos: haber sembrado el volumen de datos (Diseño §3.4.1/§3.4.2) y tener
// DATABASE_URL apuntando a la BD de pruebas (por defecto lee .env.integration).

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "pg";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, "../data/entity-ids.json");
const POOL_SIZE = Number(process.env.POOL_SIZE || 300);

function loadDatabaseUrl() {
  if (process.env.DATABASE_URL) return process.env.DATABASE_URL;
  // Fallback: parsear DATABASE_URL desde .env.integration sin dependencias.
  const envPath = resolve(__dirname, "../../../.env.integration");
  if (existsSync(envPath)) {
    const line = readFileSync(envPath, "utf8")
      .split("\n")
      .find((l) => l.startsWith("DATABASE_URL="));
    if (line) return line.slice("DATABASE_URL=".length).trim().replace(/^"|"$/g, "");
  }
  throw new Error("DATABASE_URL no está definida y no se encontró en .env.integration");
}

// tabla -> query. Los targets deben estar SIN convertir y no borrados para poder
// convertirlos en las pruebas (convertTarget es idempotente si ya se convirtió).
const QUERIES = {
  accounts: `SELECT id FROM "crm_Accounts" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  contacts: `SELECT id FROM "crm_Contacts" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  leads: `SELECT id FROM "crm_Leads" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  opportunities: `SELECT id FROM "crm_Opportunities" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  contracts: `SELECT id FROM "crm_Contracts" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  targets: `SELECT id FROM "crm_Targets" WHERE "deletedAt" IS NULL AND converted_at IS NULL ORDER BY id LIMIT $1`,
};

async function main() {
  const client = new Client({ connectionString: loadDatabaseUrl() });
  await client.connect();
  const pool = {};
  try {
    for (const [key, sql] of Object.entries(QUERIES)) {
      const { rows } = await client.query(sql, [POOL_SIZE]);
      pool[key] = rows.map((r) => r.id);
      console.log(`[collect] ${key}: ${pool[key].length} ids`);
    }
  } finally {
    await client.end();
  }
  writeFileSync(OUT, JSON.stringify(pool, null, 2));
  console.log(`[collect] escrito ${OUT}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
