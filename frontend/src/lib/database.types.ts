export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      audiobook_generations: {
        Row: {
          id: string
          title: string
          input_text: string
          input_method: 'text' | 'file'
          file_name: string | null
          audio_url: string | null
          duration: number | null
          status: 'pending' | 'processing' | 'completed' | 'failed'
          error_message: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          title: string
          input_text: string
          input_method: 'text' | 'file'
          file_name?: string | null
          audio_url?: string | null
          duration?: number | null
          status?: 'pending' | 'processing' | 'completed' | 'failed'
          error_message?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          title?: string
          input_text?: string
          input_method?: 'text' | 'file'
          file_name?: string | null
          audio_url?: string | null
          duration?: number | null
          status?: 'pending' | 'processing' | 'completed' | 'failed'
          error_message?: string | null
          created_at?: string
          updated_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}

export type AudiobookGeneration = Database['public']['Tables']['audiobook_generations']['Row'];