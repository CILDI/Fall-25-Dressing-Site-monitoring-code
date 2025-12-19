import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://xvhnrqpcgitxvumllxiu.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh2aG5ycXBjZ2l0eHZ1bWxseGl1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkzNTY1ODAsImV4cCI6MjA3NDkzMjU4MH0.fJ-9juMc4z2D6yrvz4JwvHCI7H8p7QRJHOXR2m5XXkU'

export const supabase = createClient(supabaseUrl, supabaseKey)
