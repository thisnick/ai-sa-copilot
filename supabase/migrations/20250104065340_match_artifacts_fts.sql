alter table "public"."artifact_contents" add column "parsed_text_ts_vector" tsvector;

CREATE INDEX artifact_contents_parsed_text_ts_vector_idx ON public.artifact_contents USING gin (parsed_text_ts_vector);

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.match_artifacts_fts(
  search_query text,
  match_count integer,
  domain_id uuid,
  filter jsonb
)
  RETURNS TABLE(
    artifact_id uuid,
    artifact_content_id uuid,
    metadata jsonb,
    title text,
    summary text,
    summary_embedding vector,
    anchor_id text,
    url text,
    similarity double precision
  )
  LANGUAGE plpgsql
AS $function$
BEGIN
  RETURN QUERY
  WITH results AS (
    SELECT
      artifacts.artifact_id,
      artifact_contents.artifact_content_id,
      artifact_contents.metadata,
      artifact_contents.title,
      artifact_contents.summary,
      artifact_contents.summary_embedding,
      artifact_contents.anchor_id,
      artifacts.url,
      ts_rank(
        artifact_contents.parsed_text_ts_vector,
        websearch_to_tsquery(search_query)
      )::double precision AS similarity
    FROM
      artifact_contents
      INNER JOIN artifacts ON artifact_contents.artifact_id = artifacts.artifact_id
    WHERE
      artifact_contents.metadata @> filter
      AND artifacts.domain_id = match_artifacts_fts.domain_id
      AND artifact_contents.parsed_text_ts_vector @@ websearch_to_tsquery(search_query)
  )
  SELECT *
  FROM results
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_parsed_text_ts_vector()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.parsed_text_ts_vector := to_tsvector('english', NEW.parsed_text);
    RETURN NEW;
END;
$function$
;

CREATE TRIGGER set_parsed_text_ts_vector BEFORE INSERT OR UPDATE ON public.artifact_contents FOR EACH ROW EXECUTE FUNCTION update_parsed_text_ts_vector();

UPDATE public.artifact_contents
SET
  parsed_text_ts_vector = TO_TSVECTOR('english', parsed_text);
