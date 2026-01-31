/**
 * Supabase client initialization for FionaFast frontend.
 * 
 * Reads configuration from .env.local file in project root.
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl) {
  throw new Error(
    'Missing NEXT_PUBLIC_SUPABASE_URL environment variable. ' +
    'Please set it in your .env.local file in the project root.'
  )
}

if (!supabaseAnonKey) {
  throw new Error(
    'Missing NEXT_PUBLIC_SUPABASE_ANON_KEY environment variable. ' +
    'Please set it in your .env.local file in the project root.'
  )
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

