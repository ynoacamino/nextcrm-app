import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const MANIFEST_PATH = resolve(__dirname, '../../../.next/server/server-reference-manifest.json');
const ACTION_IDS_PATH = resolve(__dirname, '../action-ids.js');

const TARGET_ACTIONS = {
  createAccount: { name: 'createAccount', file: 'create-account' },
  updateAccount: { name: 'updateAccount', file: 'update-account' },
  deleteAccount: { name: 'deleteAccount', file: 'delete-account' },
  createContact: { name: 'createContact', file: 'create-contact' },
  updateContact: { name: 'updateContact', file: 'update-contact' },
  deleteContact: { name: 'deleteContact', file: 'delete-contact' },
  convertTarget: { name: 'convertTarget', file: 'convert-target' },
  createOpportunity: { name: 'createOpportunity', file: 'create-opportunity' },
  updateOpportunity: { name: 'updateOpportunity', file: 'update-opportunity' },
  createActivity: { name: 'createActivity', file: 'create-activity' },
  addContractLineItem: { name: 'addContractLineItem', file: 'add-line-item' },
};

function main() {
  if (!existsSync(MANIFEST_PATH)) {
    console.error(`[collect-actions] Error: No se encontró el manifiesto en ${MANIFEST_PATH}`);
    console.error('Por favor, asegúrate de correr primero "pnpm run build" para compilar la aplicación.');
    process.exit(1);
  }

  console.log('[collect-actions] Cargando manifiesto de Next.js...');
  const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf8'));
  const nodeActions = manifest.node || {};

  const resolved = {};

  for (const [hash, entry] of Object.entries(nodeActions)) {
    for (const [key, spec] of Object.entries(TARGET_ACTIONS)) {
      if (entry.exportedName === spec.name && entry.filename.includes(spec.file)) {
        resolved[key] = hash;
        break;
      }
    }
  }
  const resolvedKeys = Object.keys(resolved);
  console.log(`[collect-actions] Se resolvieron ${resolvedKeys.length} de ${Object.keys(TARGET_ACTIONS).length} Server Actions.`);

  if (resolvedKeys.length === 0) {
    console.warn('[collect-actions] Advertencia: No se pudo resolver ninguna acción. ¿Es el build correcto?');
    process.exit(1);
  }

  let actionIdsContent = readFileSync(ACTION_IDS_PATH, 'utf8');
  let updatedCount = 0;

  for (const [actionName, hash] of Object.entries(resolved)) {
    const regex = new RegExp(`("${actionName}",\\s*)"(?:REEMPLAZAR_${actionName}|[0-9a-fA-F]{40,})"`, 'g');
    if (regex.test(actionIdsContent)) {
      actionIdsContent = actionIdsContent.replace(regex, `$1"${hash}"`);
      console.log(`[collect-actions] Actualizada: ${actionName} -> ${hash}`);
      updatedCount++;
    } else {
      const simpleRegex = new RegExp(`"REEMPLAZAR_${actionName}"`, 'g');
      if (simpleRegex.test(actionIdsContent)) {
        actionIdsContent = actionIdsContent.replace(simpleRegex, `"${hash}"`);
        console.log(`[collect-actions] Actualizada (fallback): ${actionName} -> ${hash}`);
        updatedCount++;
      }
    }
  }

  if (updatedCount > 0) {
    writeFileSync(ACTION_IDS_PATH, actionIdsContent, 'utf8');
    console.log(`[collect-actions] Guardado exitosamente. Se actualizaron ${updatedCount} acciones en ${ACTION_IDS_PATH}`);
  } else {
    console.log('[collect-actions] No fue necesario realizar actualizaciones en action-ids.js (los hashes ya coinciden).');
  }
}

main();
