

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pg_net" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgsodium" WITH SCHEMA "pgsodium";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA "extensions";






CREATE TYPE "public"."enum_crawl_status" AS ENUM (
    'discovered',
    'scraped',
    'scrape_failed',
    'scraping'
);


ALTER TYPE "public"."enum_crawl_status" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."detect_article_clusters"("target_domain_id" "uuid", "iterations" integer DEFAULT 10, "resolution" double precision DEFAULT 1.0) RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    total_edge_weight float;
BEGIN
    -- Create temporary edge table with weights, filtered by domain
    CREATE TEMPORARY TABLE IF NOT EXISTS temp_edges AS
    WITH consolidated_links AS (
        SELECT 
            source_artifact_id,
            a.url as target_url,
            COUNT(*) as weight
        FROM artifact_links al
        JOIN artifacts a ON al.target_url = a.url
        WHERE a.domain_id = target_domain_id
        GROUP BY source_artifact_id, a.url
    )
    SELECT 
        l.source_artifact_id as source_id,
        a.artifact_id as target_id,
        l.weight
    FROM consolidated_links l
    JOIN artifacts a ON l.target_url = a.url
    WHERE a.domain_id = target_domain_id;

    -- Get total edge weight for normalization
    SELECT SUM(weight) INTO total_edge_weight FROM temp_edges;

    -- Create temporary nodes table with total edge weight
    CREATE TEMPORARY TABLE IF NOT EXISTS temp_nodes AS
    SELECT 
        artifact_id as node_id,
        artifact_id as cluster_id,
        COALESCE(
            (SELECT SUM(weight) 
             FROM temp_edges 
             WHERE source_id = artifact_id OR target_id = artifact_id),
            0
        ) as degree
    FROM artifacts
    WHERE crawl_status = 'scraped'
    AND domain_id = target_domain_id;

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_temp_edges_source ON temp_edges USING hash (source_id);
    CREATE INDEX IF NOT EXISTS idx_temp_edges_target ON temp_edges USING hash (target_id);
    CREATE INDEX IF NOT EXISTS idx_temp_nodes_cluster ON temp_nodes USING hash (cluster_id);

    -- Record initial clusters
    INSERT INTO artifact_clusters (
        artifact_id,
        cluster_id,
        is_intermediate,
        iteration
    )
    SELECT 
        node_id,
        cluster_id,
        true,
        0
    FROM temp_nodes;

    -- Iterate Leiden algorithm
    FOR iteration IN 1..iterations LOOP
        -- Update cluster assignments
        WITH node_moves AS (
            SELECT 
                n.node_id,
                COALESCE(
                    (
                        SELECT target_cluster
                        FROM (
                            SELECT 
                                n2.cluster_id as target_cluster,
                                -- Revised modularity gain calculation
                                (
                                    -- K_ic: Edge weight to target cluster
                                    SUM(e.weight)::float 
                                    -- Subtract expected edges (a_i * K_c / 2m)
                                    - (n.degree::float * cs.total_degree::float 
                                       / (2 * total_edge_weight))
                                ) * resolution / total_edge_weight as gain
                            FROM temp_edges e
                            JOIN temp_nodes n2 ON (
                                CASE 
                                    WHEN e.source_id = n.node_id THEN e.target_id
                                    ELSE e.source_id
                                END = n2.node_id
                            )
                            JOIN (
                                SELECT 
                                    cluster_id,
                                    COUNT(*) as size,
                                    SUM(degree) as total_degree
                                FROM temp_nodes
                                GROUP BY cluster_id
                            ) cs ON n2.cluster_id = cs.cluster_id
                            WHERE e.source_id = n.node_id 
                               OR e.target_id = n.node_id
                            GROUP BY n2.cluster_id, cs.size, cs.total_degree, n.degree
                            HAVING n2.cluster_id != n.cluster_id
                            ORDER BY gain DESC
                            LIMIT 1
                        ) best_moves
                    ),
                    n.cluster_id
                ) as new_cluster
            FROM temp_nodes n
        )
        UPDATE temp_nodes n
        SET cluster_id = m.new_cluster
        FROM node_moves m
        WHERE n.node_id = m.node_id
        AND n.cluster_id != m.new_cluster;

        -- Record the state after this iteration
        INSERT INTO artifact_clusters (
            artifact_id,
            cluster_id,
            is_intermediate,
            iteration
        )
        SELECT 
            node_id,
            cluster_id,
            true,
            iteration
        FROM temp_nodes;

        -- Break if no moves were made
        IF NOT FOUND THEN
            EXIT;
        END IF;
    END LOOP;

    -- Insert final clusters (not intermediate)
    INSERT INTO artifact_clusters (
        artifact_id,
        cluster_id,
        is_intermediate,
        iteration
    )
    SELECT 
        node_id,
        cluster_id,
        false,
        iterations + 1
    FROM temp_nodes;

    -- Cleanup
    DROP TABLE IF EXISTS temp_edges;
    DROP TABLE IF EXISTS temp_nodes;
END;
$$;


ALTER FUNCTION "public"."detect_article_clusters"("target_domain_id" "uuid", "iterations" integer, "resolution" double precision) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."extract_domain"("uri" "text") RETURNS "text"
    LANGUAGE "plpgsql" IMMUTABLE STRICT
    AS $_$
DECLARE
    domain text;
BEGIN
    -- Return NULL if input is NULL or empty
    IF uri IS NULL OR uri = '' THEN
        RETURN NULL;
    END IF;

    -- Remove protocol (http://, https://, ftp://, etc.)
    domain := regexp_replace(uri, '^.*?://', '', 'i');
    
    -- Remove path, query parameters, and fragment
    domain := split_part(domain, '/', 1);
    domain := split_part(domain, '?', 1);
    domain := split_part(domain, '#', 1);
    
    -- Remove port number if present
    domain := split_part(domain, ':', 1);
    
    -- Remove leading 'www.'
    domain := regexp_replace(domain, '^www\.', '', 'i');
    
    -- Validate domain format - moved hyphen to end of character class
    IF domain ~ '^[a-zA-Z0-9][a-zA-Z0-9._-]*\.[a-zA-Z]{2,}$' THEN
        RETURN lower(domain);
    ELSE
        RETURN NULL;
    END IF;
END;
$_$;


ALTER FUNCTION "public"."extract_domain"("uri" "text") OWNER TO "postgres";


COMMENT ON FUNCTION "public"."extract_domain"("uri" "text") IS 'Extracts and returns the domain from a given URI. Returns NULL for invalid URIs. Executes with caller permissions.';



CREATE OR REPLACE FUNCTION "public"."get_cluster_summarization_data"("target_domain_id" "uuid", "target_cluster_id" "uuid", "target_iteration" integer) RETURNS TABLE("cluster_id" "uuid", "member_count" bigint, "iteration" integer, "sample_artifacts" "json", "prior_clusters" "json")
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    total_members bigint;
    artifacts_json json;
    prior_json json;
BEGIN
    -- Get member count
    SELECT COUNT(*) INTO total_members
    FROM artifact_clusters ac
    JOIN artifacts a ON ac.artifact_id = a.artifact_id
    WHERE a.domain_id = target_domain_id
    AND ac.cluster_id = target_cluster_id
    AND ac.iteration = target_iteration;

    -- Get sample artifacts
    SELECT json_agg(artifact_data) INTO artifacts_json
    FROM (
        SELECT 
            jsonb_build_object(
                'artifact_id', a.artifact_id,
                'title', a.title,
                'summary', a.summary,
                'url', a.url
            ) as artifact_data
        FROM artifact_clusters ac
        JOIN artifacts a ON ac.artifact_id = a.artifact_id
        WHERE a.domain_id = target_domain_id
        AND ac.cluster_id = target_cluster_id
        AND ac.iteration = target_iteration
        ORDER BY a.artifact_id
        LIMIT 100
    ) sample_artifacts;

    -- Get prior clusters if not at iteration 0
    IF target_iteration > 0 THEN
        SELECT json_agg(cluster_data) INTO prior_json
        FROM (
            SELECT 
                jsonb_build_object(
                    'cluster_id', ac_prior.cluster_id,
                    'member_count', COUNT(*),
                    'iteration', ac_prior.iteration
                ) as cluster_data
            FROM artifact_clusters ac_current
            JOIN artifact_clusters ac_prior 
                ON ac_current.artifact_id = ac_prior.artifact_id
                AND ac_prior.iteration = ac_current.iteration - 1
            WHERE ac_current.cluster_id = target_cluster_id
            AND ac_current.iteration = target_iteration
            GROUP BY ac_prior.cluster_id, ac_prior.iteration
        ) prior_clusters;
    END IF;

    RETURN QUERY 
    SELECT 
        target_cluster_id,
        total_members,
        target_iteration,
        COALESCE(artifacts_json, '[]'::json),
        COALESCE(prior_json, '[]'::json);
END;
$$;


ALTER FUNCTION "public"."get_cluster_summarization_data"("target_domain_id" "uuid", "target_cluster_id" "uuid", "target_iteration" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_top_level_clusters"("target_domain_id" "uuid") RETURNS TABLE("cluster_id" "uuid", "member_count" bigint, "iteration" integer)
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT 
        ac.cluster_id,
        COUNT(*) OVER (PARTITION BY ac.cluster_id) as member_count,
        ac.iteration
    FROM artifact_clusters ac
    JOIN artifacts a ON ac.artifact_id = a.artifact_id
    WHERE a.domain_id = target_domain_id
    AND ac.is_intermediate = false
    ORDER BY member_count DESC;
END;
$$;


ALTER FUNCTION "public"."get_top_level_clusters"("target_domain_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."match_artifacts"("query_embedding" "extensions"."vector", "match_count" integer, "filter" "jsonb") RETURNS TABLE("artifact_id" "uuid", "metadata" "jsonb", "title" "text", "summary" "text", "summary_embedding" "extensions"."vector", "url" "text", "similarity" double precision)
    LANGUAGE "plpgsql"
    AS $$
BEGIN     
    RETURN QUERY      
    WITH results AS (         
        SELECT             
            artifacts.artifact_id,             
            artifacts.metadata,             
            artifacts.title,             
            artifacts.summary,             
            artifacts.summary_embedding,             
            artifacts.url,             
            1 - (artifacts.summary_embedding <=> query_embedding) AS similarity         
        FROM             
            artifacts         
        WHERE             
            artifacts.metadata @> filter     
    )     
    SELECT *     
    FROM results     
    ORDER BY similarity DESC     
    LIMIT match_count; 
END;
$$;


ALTER FUNCTION "public"."match_artifacts"("query_embedding" "extensions"."vector", "match_count" integer, "filter" "jsonb") OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."artifact_clusters" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "artifact_id" "uuid" NOT NULL,
    "cluster_id" "uuid" NOT NULL,
    "is_intermediate" boolean DEFAULT true NOT NULL,
    "iteration" integer NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."artifact_clusters" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."artifact_domains" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "name" "text" NOT NULL,
    "crawl_config" "jsonb" NOT NULL
);


ALTER TABLE "public"."artifact_domains" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."artifact_links" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "source_artifact_id" "uuid" NOT NULL,
    "anchor_text" "text" DEFAULT ''::"text" NOT NULL,
    "target_url" "text" NOT NULL
);


ALTER TABLE "public"."artifact_links" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."artifacts" (
    "artifact_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "metadata" "jsonb",
    "parsed_text" "text",
    "title" "text",
    "summary" "text",
    "summary_embedding" "extensions"."vector"(768),
    "url" "text" NOT NULL,
    "crawl_depth" bigint NOT NULL,
    "crawl_status" "public"."enum_crawl_status" DEFAULT 'discovered'::"public"."enum_crawl_status" NOT NULL,
    "domain_id" "uuid" NOT NULL
);


ALTER TABLE "public"."artifacts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."cluster_summaries" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "domain_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "cluster_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "iteration" integer NOT NULL,
    "member_count" integer NOT NULL,
    "summary" "jsonb"
);


ALTER TABLE "public"."cluster_summaries" OWNER TO "postgres";


ALTER TABLE ONLY "public"."artifact_clusters"
    ADD CONSTRAINT "artifact_clusters_artifact_id_iteration_key" UNIQUE ("artifact_id", "iteration");



ALTER TABLE ONLY "public"."artifact_domains"
    ADD CONSTRAINT "artifact_domains_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."artifact_links"
    ADD CONSTRAINT "artifact_links_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."artifacts"
    ADD CONSTRAINT "artifacts_pkey" PRIMARY KEY ("artifact_id");



ALTER TABLE ONLY "public"."artifacts"
    ADD CONSTRAINT "artifacts_url_key" UNIQUE ("url");



ALTER TABLE ONLY "public"."cluster_summaries"
    ADD CONSTRAINT "cluster_summaries_pkey" PRIMARY KEY ("id");



CREATE INDEX "artifact_clusters_artifact_id_idx" ON "public"."artifact_clusters" USING "btree" ("artifact_id");



CREATE INDEX "artifact_clusters_cluster_id_idx" ON "public"."artifact_clusters" USING "btree" ("cluster_id");



CREATE INDEX "artifact_clusters_is_intermediate_idx" ON "public"."artifact_clusters" USING "btree" ("is_intermediate");



CREATE INDEX "artifact_clusters_iteration_idx" ON "public"."artifact_clusters" USING "btree" ("iteration");



CREATE INDEX "artifact_links_target_url_source_artifact_id_anchor_text_idx" ON "public"."artifact_links" USING "btree" ("target_url", "source_artifact_id", "anchor_text");



CREATE INDEX "artifacts_domain_id_idx" ON "public"."artifacts" USING "btree" ("domain_id");



CREATE INDEX "artifacts_summary_embedding_idx" ON "public"."artifacts" USING "hnsw" ("summary_embedding" "extensions"."vector_cosine_ops");



CREATE INDEX "cluster_summaries_domain_id_cluster_id_iteration_idx" ON "public"."cluster_summaries" USING "btree" ("domain_id", "cluster_id", "iteration");



ALTER TABLE ONLY "public"."artifact_clusters"
    ADD CONSTRAINT "artifact_clusters_artifact_id_fkey" FOREIGN KEY ("artifact_id") REFERENCES "public"."artifacts"("artifact_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."artifact_links"
    ADD CONSTRAINT "artifact_links_source_artifact_id_fkey" FOREIGN KEY ("source_artifact_id") REFERENCES "public"."artifacts"("artifact_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."artifacts"
    ADD CONSTRAINT "artifacts_domain_id_fkey" FOREIGN KEY ("domain_id") REFERENCES "public"."artifact_domains"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."cluster_summaries"
    ADD CONSTRAINT "cluster_summaries_domain_id_fkey" FOREIGN KEY ("domain_id") REFERENCES "public"."artifact_domains"("id") ON DELETE CASCADE;



CREATE POLICY "Allow all access to the artifacts domains table" ON "public"."artifact_domains" USING (true);



CREATE POLICY "Enable access for all users" ON "public"."artifacts" USING (true);



CREATE POLICY "Enable access to all users" ON "public"."artifact_links" USING (true);



ALTER TABLE "public"."artifact_clusters" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."artifact_domains" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."artifact_links" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."artifacts" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."cluster_summaries" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";





GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";




































































































































































































































































































































































































































































































































GRANT ALL ON FUNCTION "public"."detect_article_clusters"("target_domain_id" "uuid", "iterations" integer, "resolution" double precision) TO "anon";
GRANT ALL ON FUNCTION "public"."detect_article_clusters"("target_domain_id" "uuid", "iterations" integer, "resolution" double precision) TO "authenticated";
GRANT ALL ON FUNCTION "public"."detect_article_clusters"("target_domain_id" "uuid", "iterations" integer, "resolution" double precision) TO "service_role";



GRANT ALL ON FUNCTION "public"."extract_domain"("uri" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."extract_domain"("uri" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."extract_domain"("uri" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_cluster_summarization_data"("target_domain_id" "uuid", "target_cluster_id" "uuid", "target_iteration" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."get_cluster_summarization_data"("target_domain_id" "uuid", "target_cluster_id" "uuid", "target_iteration" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_cluster_summarization_data"("target_domain_id" "uuid", "target_cluster_id" "uuid", "target_iteration" integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."get_top_level_clusters"("target_domain_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."get_top_level_clusters"("target_domain_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_top_level_clusters"("target_domain_id" "uuid") TO "service_role";

































GRANT ALL ON TABLE "public"."artifact_clusters" TO "anon";
GRANT ALL ON TABLE "public"."artifact_clusters" TO "authenticated";
GRANT ALL ON TABLE "public"."artifact_clusters" TO "service_role";



GRANT ALL ON TABLE "public"."artifact_domains" TO "anon";
GRANT ALL ON TABLE "public"."artifact_domains" TO "authenticated";
GRANT ALL ON TABLE "public"."artifact_domains" TO "service_role";



GRANT ALL ON TABLE "public"."artifact_links" TO "anon";
GRANT ALL ON TABLE "public"."artifact_links" TO "authenticated";
GRANT ALL ON TABLE "public"."artifact_links" TO "service_role";



GRANT ALL ON TABLE "public"."artifacts" TO "anon";
GRANT ALL ON TABLE "public"."artifacts" TO "authenticated";
GRANT ALL ON TABLE "public"."artifacts" TO "service_role";



GRANT ALL ON TABLE "public"."cluster_summaries" TO "anon";
GRANT ALL ON TABLE "public"."cluster_summaries" TO "authenticated";
GRANT ALL ON TABLE "public"."cluster_summaries" TO "service_role";



ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";






























RESET ALL;
