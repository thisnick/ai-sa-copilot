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
      artifact_clusters: {
        Row: {
          artifact_id: string
          cluster_id: string
          created_at: string
          id: string
          is_intermediate: boolean
          iteration: number
        }
        Insert: {
          artifact_id: string
          cluster_id: string
          created_at?: string
          id?: string
          is_intermediate?: boolean
          iteration: number
        }
        Update: {
          artifact_id?: string
          cluster_id?: string
          created_at?: string
          id?: string
          is_intermediate?: boolean
          iteration?: number
        }
        Relationships: [
          {
            foreignKeyName: "artifact_clusters_artifact_id_fkey"
            columns: ["artifact_id"]
            isOneToOne: false
            referencedRelation: "artifacts"
            referencedColumns: ["artifact_id"]
          },
        ]
      }
      artifact_contents: {
        Row: {
          anchor_id: string | null
          artifact_content_id: string
          artifact_id: string
          created_at: string
          metadata: Json | null
          parsed_text: string
          parsed_text_ts_vector: unknown | null
          summary: string
          summary_embedding: string
          title: string | null
        }
        Insert: {
          anchor_id?: string | null
          artifact_content_id?: string
          artifact_id: string
          created_at?: string
          metadata?: Json | null
          parsed_text: string
          parsed_text_ts_vector?: unknown | null
          summary: string
          summary_embedding: string
          title?: string | null
        }
        Update: {
          anchor_id?: string | null
          artifact_content_id?: string
          artifact_id?: string
          created_at?: string
          metadata?: Json | null
          parsed_text?: string
          parsed_text_ts_vector?: unknown | null
          summary?: string
          summary_embedding?: string
          title?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "artifact_contents_artifact_id_fkey"
            columns: ["artifact_id"]
            isOneToOne: false
            referencedRelation: "artifacts"
            referencedColumns: ["artifact_id"]
          },
        ]
      }
      artifact_domains: {
        Row: {
          config: Json
          created_at: string
          id: string
          name: string
          visibility: Database["public"]["Enums"]["domain_visibility"]
        }
        Insert: {
          config: Json
          created_at?: string
          id?: string
          name: string
          visibility?: Database["public"]["Enums"]["domain_visibility"]
        }
        Update: {
          config?: Json
          created_at?: string
          id?: string
          name?: string
          visibility?: Database["public"]["Enums"]["domain_visibility"]
        }
        Relationships: []
      }
      artifact_links: {
        Row: {
          anchor_text: string
          created_at: string
          id: string
          source_artifact_content_id: string
          target_url: string
        }
        Insert: {
          anchor_text?: string
          created_at?: string
          id?: string
          source_artifact_content_id: string
          target_url: string
        }
        Update: {
          anchor_text?: string
          created_at?: string
          id?: string
          source_artifact_content_id?: string
          target_url?: string
        }
        Relationships: [
          {
            foreignKeyName: "artifact_links_source_artifact_content_id_fkey"
            columns: ["source_artifact_content_id"]
            isOneToOne: false
            referencedRelation: "artifact_contents"
            referencedColumns: ["artifact_content_id"]
          },
        ]
      }
      artifacts: {
        Row: {
          artifact_id: string
          content_sha256: string | null
          crawl_depth: number
          crawl_status: Database["public"]["Enums"]["enum_crawl_status"]
          crawled_as_artifact_id: string | null
          created_at: string
          domain_id: string
          metadata: Json | null
          parsed_text: string | null
          summary: string | null
          title: string | null
          url: string
        }
        Insert: {
          artifact_id?: string
          content_sha256?: string | null
          crawl_depth: number
          crawl_status?: Database["public"]["Enums"]["enum_crawl_status"]
          crawled_as_artifact_id?: string | null
          created_at?: string
          domain_id: string
          metadata?: Json | null
          parsed_text?: string | null
          summary?: string | null
          title?: string | null
          url: string
        }
        Update: {
          artifact_id?: string
          content_sha256?: string | null
          crawl_depth?: number
          crawl_status?: Database["public"]["Enums"]["enum_crawl_status"]
          crawled_as_artifact_id?: string | null
          created_at?: string
          domain_id?: string
          metadata?: Json | null
          parsed_text?: string | null
          summary?: string | null
          title?: string | null
          url?: string
        }
        Relationships: [
          {
            foreignKeyName: "artifacts_crawled_as_artifact_id_fkey"
            columns: ["crawled_as_artifact_id"]
            isOneToOne: false
            referencedRelation: "artifacts"
            referencedColumns: ["artifact_id"]
          },
          {
            foreignKeyName: "artifacts_domain_id_fkey"
            columns: ["domain_id"]
            isOneToOne: false
            referencedRelation: "artifact_domains"
            referencedColumns: ["id"]
          },
        ]
      }
      artifacts_backup: {
        Row: {
          artifact_id: string | null
          crawl_depth: number | null
          crawl_status: Database["public"]["Enums"]["enum_crawl_status"] | null
          created_at: string | null
          domain_id: string | null
          metadata: Json | null
          parsed_text: string | null
          summary: string | null
          summary_embedding: string | null
          title: string | null
          url: string | null
        }
        Insert: {
          artifact_id?: string | null
          crawl_depth?: number | null
          crawl_status?: Database["public"]["Enums"]["enum_crawl_status"] | null
          created_at?: string | null
          domain_id?: string | null
          metadata?: Json | null
          parsed_text?: string | null
          summary?: string | null
          summary_embedding?: string | null
          title?: string | null
          url?: string | null
        }
        Update: {
          artifact_id?: string | null
          crawl_depth?: number | null
          crawl_status?: Database["public"]["Enums"]["enum_crawl_status"] | null
          created_at?: string | null
          domain_id?: string | null
          metadata?: Json | null
          parsed_text?: string | null
          summary?: string | null
          summary_embedding?: string | null
          title?: string | null
          url?: string | null
        }
        Relationships: []
      }
      cluster_summaries: {
        Row: {
          cluster_id: string
          created_at: string
          domain_id: string
          id: string
          iteration: number
          member_count: number
          summary: Json | null
        }
        Insert: {
          cluster_id?: string
          created_at?: string
          domain_id?: string
          id?: string
          iteration: number
          member_count: number
          summary?: Json | null
        }
        Update: {
          cluster_id?: string
          created_at?: string
          domain_id?: string
          id?: string
          iteration?: number
          member_count?: number
          summary?: Json | null
        }
        Relationships: [
          {
            foreignKeyName: "cluster_summaries_domain_id_fkey"
            columns: ["domain_id"]
            isOneToOne: false
            referencedRelation: "artifact_domains"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          created_at: string
          email: string
          name: string
          user_id: string
        }
        Insert: {
          created_at?: string
          email: string
          name: string
          user_id: string
        }
        Update: {
          created_at?: string
          email?: string
          name?: string
          user_id?: string
        }
        Relationships: []
      }
      thread_states: {
        Row: {
          agent_name: string | null
          context_variables: Json
          created_at: string
          messages: Json
          thread_id: string
          thread_state_id: string
        }
        Insert: {
          agent_name?: string | null
          context_variables: Json
          created_at?: string
          messages: Json
          thread_id: string
          thread_state_id?: string
        }
        Update: {
          agent_name?: string | null
          context_variables?: Json
          created_at?: string
          messages?: Json
          thread_id?: string
          thread_state_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "thread_states_thread_id_fkey"
            columns: ["thread_id"]
            isOneToOne: false
            referencedRelation: "threads"
            referencedColumns: ["thread_id"]
          },
        ]
      }
      threads: {
        Row: {
          created_at: string
          last_known_good_thread_state_id: string | null
          thread_id: string
          thread_type: Database["public"]["Enums"]["enum_thread_type"]
          title: string | null
          user_id: string
        }
        Insert: {
          created_at?: string
          last_known_good_thread_state_id?: string | null
          thread_id?: string
          thread_type: Database["public"]["Enums"]["enum_thread_type"]
          title?: string | null
          user_id: string
        }
        Update: {
          created_at?: string
          last_known_good_thread_state_id?: string | null
          thread_id?: string
          thread_type?: Database["public"]["Enums"]["enum_thread_type"]
          title?: string | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "threads_last_known_good_thread_state_id_fkey"
            columns: ["last_known_good_thread_state_id"]
            isOneToOne: false
            referencedRelation: "thread_states"
            referencedColumns: ["thread_state_id"]
          },
          {
            foreignKeyName: "threads_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["user_id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      copy_domain_artifacts: {
        Args: {
          source_domain_id: string
          target_domain_id: string
        }
        Returns: number
      }
      detect_article_clusters: {
        Args: {
          target_domain_id: string
          iterations?: number
          resolution?: number
        }
        Returns: undefined
      }
      extract_domain: {
        Args: {
          uri: string
        }
        Returns: string
      }
      get_artifacts_with_links: {
        Args: {
          artifact_content_ids: string[]
          max_links?: number
        }
        Returns: {
          artifact_id: string
          artifact_content_id: string
          url: string
          title: string
          summary: string
          parsed_text: string
          metadata: Json
          outbound_links: Json
          inbound_links: Json
        }[]
      }
      get_cluster_summarization_data: {
        Args: {
          target_domain_id: string
          target_cluster_id: string
          target_iteration: number
        }
        Returns: {
          cluster_id: string
          member_count: number
          iteration: number
          sample_artifacts: Json
          prior_clusters: Json
        }[]
      }
      get_top_level_clusters: {
        Args: {
          target_domain_id: string
        }
        Returns: {
          cluster_id: string
          member_count: number
          iteration: number
          summary: Json
        }[]
      }
      match_artifacts: {
        Args: {
          query_embedding: string
          match_count: number
          domain_id: string
          filter: Json
        }
        Returns: {
          artifact_id: string
          artifact_content_id: string
          metadata: Json
          title: string
          summary: string
          summary_embedding: string
          anchor_id: string
          url: string
          similarity: number
        }[]
      }
      match_artifacts_fts: {
        Args: {
          search_query: string
          match_count: number
          domain_id: string
          filter: Json
        }
        Returns: {
          artifact_id: string
          artifact_content_id: string
          metadata: Json
          title: string
          summary: string
          summary_embedding: string
          anchor_id: string
          url: string
          similarity: number
        }[]
      }
    }
    Enums: {
      domain_visibility: "public" | "unreleased"
      enum_crawl_status: "discovered" | "scraped" | "scrape_failed" | "scraping"
      enum_thread_type: "runbook_generator"
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

