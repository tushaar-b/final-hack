import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

const _baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
// Normalise: ensure /api suffix
export const API_URL = _baseUrl.endsWith('/api') ? _baseUrl : `${_baseUrl}/api`
