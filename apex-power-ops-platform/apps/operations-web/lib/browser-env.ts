export const browserEnv = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL ?? '',
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? '',
  controlPlaneBaseUrl: process.env.NEXT_PUBLIC_CONTROL_PLANE_BASE_URL ?? 'http://localhost:8000',
}

export const hasSupabaseBrowserConfig =
  browserEnv.supabaseUrl.length > 0 && browserEnv.supabaseAnonKey.length > 0