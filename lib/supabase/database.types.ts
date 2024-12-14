export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  graphql_public: {
    Tables: {
      [_ in never]: never
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      graphql: {
        Args: {
          operationName?: string
          query?: string
          variables?: Json
          extensions?: Json
        }
        Returns: Json
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
  public: {
    Tables: {
      artifact_links: {
        Row: {
          anchor_text: string
          created_at: string
          id: string
          source_artifact_id: string
          target_url: string
        }
        Insert: {
          anchor_text?: string
          created_at?: string
          id?: string
          source_artifact_id: string
          target_url: string
        }
        Update: {
          anchor_text?: string
          created_at?: string
          id?: string
          source_artifact_id?: string
          target_url?: string
        }
        Relationships: [
          {
            foreignKeyName: "artifact_links_source_artifact_id_fkey"
            columns: ["source_artifact_id"]
            isOneToOne: false
            referencedRelation: "artifacts"
            referencedColumns: ["artifact_id"]
          },
        ]
      }
      artifact_sections: {
        Row: {
          artifact_id: string
          created_at: string
          heading: string
          metadata: Json | null
          parsed_text: string | null
          section_id: number
          summary: string
          summary_embedding: string | null
        }
        Insert: {
          artifact_id: string
          created_at?: string
          heading: string
          metadata?: Json | null
          parsed_text?: string | null
          section_id?: never
          summary: string
          summary_embedding?: string | null
        }
        Update: {
          artifact_id?: string
          created_at?: string
          heading?: string
          metadata?: Json | null
          parsed_text?: string | null
          section_id?: never
          summary?: string
          summary_embedding?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "fk_artifacts"
            columns: ["artifact_id"]
            isOneToOne: false
            referencedRelation: "artifacts"
            referencedColumns: ["artifact_id"]
          },
        ]
      }
      artifacts: {
        Row: {
          artifact_id: string
          crawl_depth: number
          crawl_status: Database["public"]["Enums"]["enum_crawl_status"]
          created_at: string
          metadata: Json | null
          parsed_text: string | null
          summary: string | null
          summary_embedding: string | null
          title: string | null
          url: string
        }
        Insert: {
          artifact_id?: string
          crawl_depth: number
          crawl_status?: Database["public"]["Enums"]["enum_crawl_status"]
          created_at?: string
          metadata?: Json | null
          parsed_text?: string | null
          summary?: string | null
          summary_embedding?: string | null
          title?: string | null
          url: string
        }
        Update: {
          artifact_id?: string
          crawl_depth?: number
          crawl_status?: Database["public"]["Enums"]["enum_crawl_status"]
          created_at?: string
          metadata?: Json | null
          parsed_text?: string | null
          summary?: string | null
          summary_embedding?: string | null
          title?: string | null
          url?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      extract_domain: {
        Args: {
          uri: string
        }
        Returns: string
      }
      match_artifacts: {
        Args: {
          query_embedding: string
          match_count: number
          filter: Json
        }
        Returns: {
          artifact_id: string
          metadata: Json
          parsed_text: string
          title: string
          summary: string
          summary_embedding: string
          url: string
          similarity: number
        }[]
      }
    }
    Enums: {
      enum_crawl_status: "discovered" | "scraped" | "scrape_failed" | "scraping"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type PublicSchema = Database[Extract<keyof Database, "public">]

export type Tables<
  PublicTableNameOrOptions extends
    | keyof (PublicSchema["Tables"] & PublicSchema["Views"])
    | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
        Database[PublicTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
      Database[PublicTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : PublicTableNameOrOptions extends keyof (PublicSchema["Tables"] &
        PublicSchema["Views"])
    ? (PublicSchema["Tables"] &
        PublicSchema["Views"])[PublicTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  PublicTableNameOrOptions extends
    | keyof PublicSchema["Tables"]
    | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : PublicTableNameOrOptions extends keyof PublicSchema["Tables"]
    ? PublicSchema["Tables"][PublicTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  PublicTableNameOrOptions extends
    | keyof PublicSchema["Tables"]
    | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : PublicTableNameOrOptions extends keyof PublicSchema["Tables"]
    ? PublicSchema["Tables"][PublicTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  PublicEnumNameOrOptions extends
    | keyof PublicSchema["Enums"]
    | { schema: keyof Database },
  EnumName extends PublicEnumNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = PublicEnumNameOrOptions extends { schema: keyof Database }
  ? Database[PublicEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : PublicEnumNameOrOptions extends keyof PublicSchema["Enums"]
    ? PublicSchema["Enums"][PublicEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof PublicSchema["CompositeTypes"]
    | { schema: keyof Database },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof Database }
  ? Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof PublicSchema["CompositeTypes"]
    ? PublicSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

