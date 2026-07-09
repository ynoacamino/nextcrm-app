

function fromEnv(name, fallback) {
  return __ENV[`AID_${name}`] || fallback;
}

export const ACTION_IDS = {
  
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
