import { createClient, type SupabaseClient } from "@supabase/supabase-js";

/**
 * Cliente Supabase do navegador. Usa SOMENTE a chave pública (publishable/anon):
 * o acesso é limitado por RLS e pela função create_order (database/migrations/003).
 * NUNCA coloque a secret/service_role key em variáveis VITE_ (vão para o bundle público).
 */
const url = import.meta.env.VITE_SUPABASE_URL ?? "https://lvukeuyexxewmnslucwj.supabase.co";
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

let client: SupabaseClient | null | undefined;

export function getSupabase(): SupabaseClient | null {
  if (client === undefined) {
    if (key && /^sb_secret_|service_role/i.test(key)) {
      console.error("VITE_SUPABASE_PUBLISHABLE_KEY contém uma chave SECRETA. Use a publishable key.");
      client = null;
    } else {
      client = key ? createClient(url, key) : null;
    }
  }
  return client;
}

export const SUPABASE_NOT_CONFIGURED =
  "Login e pedidos indisponíveis: configure VITE_SUPABASE_PUBLISHABLE_KEY no Netlify.";
