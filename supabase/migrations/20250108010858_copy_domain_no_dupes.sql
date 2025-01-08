set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.copy_domain_artifacts(source_domain_id uuid, target_domain_id uuid)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$DECLARE
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
        WHERE domain_id = source_domain_id AND
              crawled_as_artifact_id IS NULL
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
END;$function$
;


