

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "pg";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, "../data/entity-ids.json");
const POOL_SIZE = Number(process.env.POOL_SIZE || 300);

function loadDatabaseUrl() {
  if (process.env.DATABASE_URL) return process.env.DATABASE_URL;
  
  const envPath = resolve(__dirname, "../../../.env.test");
  if (existsSync(envPath)) {
    const line = readFileSync(envPath, "utf8")
      .split("\n")
      .find((l) => l.startsWith("DATABASE_URL="));
    if (line) return line.slice("DATABASE_URL=".length).trim().replace(/^"|"$/g, "");
  }
  throw new Error("DATABASE_URL no está definida y no se encontró en .env.test");
}

const QUERIES = {
  accounts: `SELECT id FROM "crm_Accounts" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  contacts: `SELECT id FROM "crm_Contacts" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  leads: `SELECT id FROM "crm_Leads" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  opportunities: `SELECT id FROM "crm_Opportunities" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  contracts: `SELECT id FROM "crm_Contracts" WHERE "deletedAt" IS NULL ORDER BY id LIMIT $1`,
  targets: `SELECT id FROM "crm_Targets" WHERE "deletedAt" IS NULL AND converted_at IS NULL ORDER BY id LIMIT $1`,
};

async function main() {
  const dbUrl = loadDatabaseUrl();
  const maskedUrl = dbUrl.replace(/:\/\/([^:]+):([^@]+)@/, '://$1:***@');
  console.log(`[collect] conectando a ${maskedUrl}`);

  const client = new Client({ connectionString: dbUrl });
  await client.connect();
  console.log(`[collect] conexión exitosa`);

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

  const totalIds = Object.values(pool).reduce((s, arr) => s + arr.length, 0);
  if (totalIds === 0) {
    console.error('[collect] WARN: 0 IDs encontrados en total.');
    console.error('[collect] Verifica que prisma db seed se ejecutó correctamente.');
  }

  writeFileSync(OUT, JSON.stringify(pool, null, 2));
  console.log(`[collect] escrito ${OUT} (${totalIds} IDs totales)`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
