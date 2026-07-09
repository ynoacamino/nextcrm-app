// Mapa estático nombreServerAction -> hash del header `Next-Action`.
//
// Diseño de Casos de Prueba de Rendimiento §4.5 — "Estrategia de invocación de
// Server Actions desde k6".
//
// Las Server Actions de Next.js no exponen una URL por operación: todas se
// invocan con POST a la URL de la página que las contiene y se distinguen por
// el header `Next-Action`, cuyo valor es un hash cifrado. Por defecto Next
// recalcula ese hash en cada build, así que para las pruebas de rendimiento se
// fija la clave de cifrado con la variable de entorno
// `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` en el build de staging. Con la clave
// fija, el hash es estable entre builds mientras no cambie el código de la
// acción.
//
// PROCEDIMIENTO PARA CAPTURAR/ACTUALIZAR LOS IDs (§4.5):
//   1. openssl rand -base64 32  -> NEXT_SERVER_ACTIONS_ENCRYPTION_KEY (una vez).
//   2. Compilar el build de staging con esa clave fija.
//   3. Ejecutar manualmente cada operación crítica y copiar el valor del header
//      `Next-Action` desde la pestaña de red del navegador.
//   4. Pegar el hash en la clave correspondiente de este mapa y versionarlo.
//
// RIESGO R-10: si se modifica el código de una Server Action, su hash cambia
// aunque la clave de cifrado sea fija. Recapturar el ID afectado antes de
// reanudar la suite.
//
// Los IDs marcados como "REEMPLAZAR" son placeholders: deben sustituirse por
// los hashes reales capturados en el entorno de staging antes de ejecutar las
// pruebas de escritura. Se pueden pasar por -e para no versionar hashes de un
// entorno concreto, p.ej. `-e AID_createContact=00bd59...`.

function fromEnv(name, fallback) {
  return __ENV[`AID_${name}`] || fallback;
}

export const ACTION_IDS = {
  // Escrituras (POST con header Next-Action).
  createAccount: fromEnv("createAccount", "402e2d331847e9f05bf04cc199f9f81f4015ac027f"),
  updateAccount: fromEnv("updateAccount", "40ca8081de1d47eebfd2edbac2796dcb26cba1bbdd"),
  deleteAccount: fromEnv("deleteAccount", "400d47442671e85a366673c80cce4fa259474d5156"),
  createContact: fromEnv("createContact", "401d6d1ea99e398d7224ef9cbe5b5d808d5683c9fb"),
  updateContact: fromEnv("updateContact", "40ff8963bc173b37cebb9903a2330622515eec506f"),
  deleteContact: fromEnv("deleteContact", "40184ad79c5faeb3804a1875531e926d32aff9a16d"),
  convertTarget: fromEnv("convertTarget", "40651fa3dc964581dd19990fa237e785399fc5e29c"),
  createOpportunity: fromEnv("createOpportunity", "406b02a8edcd4ac84e262cebeca29710f9ba37e738"),
  updateOpportunity: fromEnv("updateOpportunity", "40ab27dadf6ad0237ba04b19f7b287bec43e5e755c"),
  createActivity: fromEnv("createActivity", "40dc83e69acf3d8b379453f69d26bc271b8a16b948"),
  addContractLineItem: fromEnv("addContractLineItem", "7f76f6e16eea6e2bfea7c06b6efa1523367f44dd8a"),
};

// Devuelve el hash de una acción y avisa si sigue siendo un placeholder.
export function actionId(name) {
  const id = ACTION_IDS[name];
  if (!id || id.startsWith("REEMPLAZAR_")) {
    console.warn(
      `[action-ids] "${name}" no tiene un Next-Action ID real. ` +
        `Captúralo en staging (Diseño §4.5) o pásalo con -e AID_${name}=<hash>.`,
    );
  }
  return id;
}
