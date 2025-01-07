create type "public"."domain_visibility" as enum ('public', 'unreleased');

alter table "public"."artifacts" drop constraint "artifacts_url_key";

drop index if exists "public"."artifacts_url_key";

alter table "public"."artifact_domains" add column "visibility" domain_visibility not null default 'public'::domain_visibility;

CREATE UNIQUE INDEX artifacts_domain_id_url_key ON public.artifacts USING btree (domain_id, url);

alter table "public"."artifacts" add constraint "artifacts_domain_id_url_key" UNIQUE using index "artifacts_domain_id_url_key";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.copy_domain_artifacts(source_domain_id uuid, target_domain_id uuid)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    rows_copied INTEGER;
BEGIN
    WITH upserted_rows AS (
        INSERT INTO public.artifacts (
            artifact_id,
            created_at,
            metadata,
            parsed_text,
            title,
            summary,
            url,
            crawl_depth,
            crawl_status,
            domain_id,
            content_sha256,
            crawled_as_artifact_id
        )
        SELECT
            gen_random_uuid(),      -- Generate a new artifact_id
            created_at,
            metadata,
            parsed_text,
            title,
            summary,
            url,
            crawl_depth,
            crawl_status,
            target_domain_id,       -- Use the target domain
            content_sha256,
            NULL
        FROM public.artifacts
        WHERE domain_id = source_domain_id
        ON CONFLICT (domain_id, url) DO UPDATE
            SET metadata               = EXCLUDED.metadata,
                parsed_text            = EXCLUDED.parsed_text,
                title                  = EXCLUDED.title,
                summary                = EXCLUDED.summary,
                crawl_depth            = EXCLUDED.crawl_depth,
                crawl_status           = EXCLUDED.crawl_status,
                content_sha256         = EXCLUDED.content_sha256,
                crawled_as_artifact_id = EXCLUDED.crawled_as_artifact_id
        RETURNING 1
    )
    SELECT COUNT(*) INTO rows_copied
    FROM upserted_rows;

    RAISE NOTICE 'Artifacts upserted from domain % to domain %: % rows affected.',
        source_domain_id,
        target_domain_id,
        rows_copied;

    RETURN rows_copied;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_artifacts_with_links(artifact_content_ids uuid[], max_links integer DEFAULT 10)
 RETURNS TABLE(artifact_id uuid, artifact_content_id uuid, url text, title text, summary text, parsed_text text, metadata jsonb, outbound_links jsonb, inbound_links jsonb)
 LANGUAGE plpgsql
AS $function$BEGIN
   RETURN QUERY
   SELECT
     ac.artifact_id,
     ac.artifact_content_id,
     a.url,
     ac.title,
     ac.summary,
     ac.parsed_text,
     ac.metadata,
     COALESCE(
       (
         SELECT jsonb_agg(outbound)
         FROM (
           SELECT DISTINCT ON (al.target_url) jsonb_build_object(
             'artifact_id', target.artifact_id,
             'url', target.url,
             'title', target.title,
             'summary', target.summary
           ) AS outbound
           FROM artifact_links al
             LEFT JOIN artifacts target ON al.target_url = target.url
           WHERE al.source_artifact_content_id = ac.artifact_content_id
           ORDER BY al.target_url
           LIMIT max_links
         ) AS outbound_links
       ),
       '[]'::jsonb
     ) AS outbound_links,
     COALESCE(
       (
         SELECT jsonb_agg(inbound)
         FROM (
           SELECT DISTINCT ON (il.source_artifact_content_id) jsonb_build_object(
             'artifact_content_id', il.source_artifact_content_id,
             'url', source_artifact.url,
             'title', source_content.title,
             'summary', source_content.summary
           ) AS inbound
           FROM artifact_links il
             LEFT JOIN artifact_contents source_content ON il.source_artifact_content_id = source_content.artifact_content_id
             LEFT JOIN artifacts source_artifact ON source_content.artifact_id = source_artifact.artifact_id
           WHERE il.target_url = a.url AND source_artifact.domain_id = a.domain_id
           ORDER BY il.source_artifact_content_id
           LIMIT max_links
         ) AS inbound_links
       ),
       '[]'::jsonb
     ) AS inbound_links
   FROM artifact_contents ac
   JOIN artifacts a ON ac.artifact_id = a.artifact_id
   WHERE ac.artifact_content_id = ANY(artifact_content_ids);
 END;$function$
;

ALTER TABLE public.artifact_domains
RENAME COLUMN crawl_config TO config;
