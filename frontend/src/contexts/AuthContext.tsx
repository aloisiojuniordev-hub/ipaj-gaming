import type { User as SupabaseUser } from "@supabase/supabase-js";
import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { getSupabase, SUPABASE_NOT_CONFIGURED } from "../services/supabase";
import type { User } from "../types";

export interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  /** Retorna needsConfirmation=true se o Supabase exigir confirmação por e-mail. */
  register: (name: string, email: string, password: string) => Promise<{ needsConfirmation: boolean }>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

const toUser = (u: SupabaseUser | null | undefined): User | null => (u ? {
  id: u.id,
  email: u.email ?? "",
  name: (u.user_metadata?.name as string | undefined) || (u.email ?? "").split("@")[0],
  created_at: u.created_at,
} : null);

// Mensagens do Supabase Auth em português.
const MESSAGES: [RegExp, string][] = [
  [/invalid login credentials/i, "E-mail ou senha inválidos."],
  [/email not confirmed/i, "Confirme seu e-mail (veja a caixa de entrada) antes de entrar."],
  [/already registered|already exists/i, "E-mail já cadastrado."],
  [/password should be at least/i, "A senha é curta demais."],
  [/rate limit|too many/i, "Muitas tentativas. Aguarde alguns minutos."],
];
const translate = (msg: string) => MESSAGES.find(([re]) => re.test(msg))?.[1] ?? msg;

function client() {
  const sb = getSupabase();
  if (!sb) throw new Error(SUPABASE_NOT_CONFIGURED);
  return sb;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(() => !!getSupabase());

  useEffect(() => {
    const sb = getSupabase();
    if (!sb) return;
    sb.auth.getSession().then(({ data }) => {
      setUser(toUser(data.session?.user));
      setLoading(false);
    });
    const { data } = sb.auth.onAuthStateChange((_event, session) => setUser(toUser(session?.user)));
    return () => data.subscription.unsubscribe();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data, error } = await client().auth.signInWithPassword({ email: email.trim().toLowerCase(), password });
    if (error) throw new Error(translate(error.message));
    setUser(toUser(data.user));
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    const { data, error } = await client().auth.signUp({
      email: email.trim().toLowerCase(), password,
      options: { data: { name: name.trim() }, emailRedirectTo: window.location.origin },
    });
    if (error) throw new Error(translate(error.message));
    if (data.session) setUser(toUser(data.user));
    return { needsConfirmation: !data.session };
  }, []);

  const logout = useCallback(async () => {
    await getSupabase()?.auth.signOut();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, login, register, logout }), [user, loading, login, register, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
