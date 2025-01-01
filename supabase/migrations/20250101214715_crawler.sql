drop function if exists "public"."match_artifacts"(query_embedding vector, match_count integer, filter jsonb);

alter table "public"."artifacts" add column "content_sha256" text;

alter table "public"."artifacts" add column "crawled_as_artifact_id" uuid;

CREATE UNIQUE INDEX artifact_contents_artifact_id_anchor_id_key ON public.artifact_contents USING btree (artifact_id, anchor_id);

CREATE INDEX artifacts_content_sha256_idx ON public.artifacts USING btree (content_sha256);

alter table "public"."artifact_contents" add constraint "artifact_contents_artifact_id_anchor_id_key" UNIQUE using index "artifact_contents_artifact_id_anchor_id_key";

alter table "public"."artifacts" add constraint "artifacts_crawled_as_artifact_id_fkey" FOREIGN KEY (crawled_as_artifact_id) REFERENCES artifacts(artifact_id) ON DELETE SET NULL not valid;

alter table "public"."artifacts" validate constraint "artifacts_crawled_as_artifact_id_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.match_artifacts(query_embedding vector, match_count integer, domain_id text, filter jsonb)
 RETURNS TABLE(artifact_id uuid, artifact_content_id uuid, metadata jsonb, title text, summary text, summary_embedding vector, anchor_id text, url text, similarity double precision)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH results AS (
        SELECT
            artifacts.artifact_id,  -- Correctly selecting artifact_id from artifacts
            artifact_contents.artifact_content_id,
            artifact_contents.metadata,
            artifact_contents.title,
            artifact_contents.summary,
            artifact_contents.summary_embedding,
            artifact_contents.anchor_id,
            artifacts.url,
            1 - (artifact_contents.summary_embedding <=> query_embedding) AS similarity
        FROM
            artifact_contents
        INNER JOIN artifacts ON artifact_contents.artifact_id = artifacts.artifact_id
        WHERE
            artifact_contents.metadata @> filter AND
            artifacts.domain_id = domain_id
    )
    SELECT *
    FROM results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$function$
;


