drop policy "Allow all users to access clusters" on "public"."artifact_clusters";

drop policy "Allow all access to the artifacts domains table" on "public"."artifact_domains";

drop policy "Enable access to all users" on "public"."artifact_links";

drop policy "Enable access for all users" on "public"."artifacts";

drop policy "Allow all users to access summaries" on "public"."cluster_summaries";

drop function if exists "public"."get_artifacts_with_links"(artifact_ids uuid[], max_links integer);

drop function if exists "public"."match_artifacts"(query_embedding vector, match_count integer, filter jsonb);

drop index if exists "public"."artifacts_summary_embedding_idx";

drop index if exists "public"."artifact_links_target_url_source_artifact_id_anchor_text_idx";

create table "public"."artifact_contents" (
    "artifact_content_id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone not null default now(),
    "artifact_id" uuid not null,
    "metadata" jsonb,
    "parsed_text" text not null,
    "anchor_id" text,
    "title" text,
    "summary" text not null,
    "summary_embedding" vector(768) not null
);


CREATE TABLE IF NOT EXISTS public.artifacts_backup AS
SELECT * FROM public.artifacts;

INSERT
INTO
  public.artifact_contents (
    artifact_id,
    created_at,
    metadata,
    parsed_text,
    title,
    summary
  )
SELECT
  artifact_id,
  created_at,
  metadata,
  parsed_text,
  title,
  summary
FROM
  public.artifacts
WHERE
  parsed_text IS NOT NULL;

alter table "public"."artifact_contents" enable row level security;

ALTER TABLE public.artifact_links
DROP CONSTRAINT artifact_links_source_artifact_id_fkey;

ALTER TABLE public.artifact_links
RENAME COLUMN source_artifact_id TO source_artifact_content_id;

alter table "public"."artifacts" drop column "summary_embedding";

CREATE INDEX artifact_contents_artifact_id_idx ON public.artifact_contents USING btree (artifact_id);

CREATE UNIQUE INDEX artifact_contents_pkey ON public.artifact_contents USING btree (artifact_content_id);

CREATE INDEX artifact_contents_summary_embedding_idx ON public.artifact_contents USING hnsw (summary_embedding vector_cosine_ops);

CREATE INDEX artifact_links_target_url_source_artifact_id_anchor_text_idx ON public.artifact_links USING btree (target_url, source_artifact_content_id, anchor_text);

alter table "public"."artifact_contents" add constraint "artifact_contents_pkey" PRIMARY KEY using index "artifact_contents_pkey";

alter table "public"."artifact_contents" add constraint "artifact_contents_artifact_id_fkey" FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id) ON DELETE CASCADE not valid;

alter table "public"."artifact_contents" validate constraint "artifact_contents_artifact_id_fkey";

alter table "public"."artifact_links" add constraint "artifact_links_source_artifact_content_id_fkey" FOREIGN KEY (source_artifact_content_id) REFERENCES artifact_contents(artifact_content_id) ON DELETE CASCADE not valid;

alter table "public"."artifact_links" validate constraint "artifact_links_source_artifact_content_id_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.get_artifacts_with_links(artifact_content_ids uuid[], max_links integer DEFAULT 10)
 RETURNS TABLE(artifact_id uuid, artifact_content_id uuid, url text, title text, summary text, parsed_text text, metadata jsonb, outbound_links jsonb, inbound_links jsonb)
 LANGUAGE plpgsql
AS $function$
 BEGIN
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
           WHERE il.target_url = a.url
           ORDER BY il.source_artifact_content_id
           LIMIT max_links
         ) AS inbound_links
       ),
       '[]'::jsonb
     ) AS inbound_links
   FROM artifact_contents ac
   JOIN artifacts a ON ac.artifact_id = a.artifact_id
   WHERE ac.artifact_content_id = ANY(artifact_content_ids);
 END;
$function$
;

CREATE OR REPLACE FUNCTION public.match_artifacts(query_embedding vector, match_count integer, filter jsonb)
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
            artifact_contents.metadata @> filter
    )
    SELECT *
    FROM results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$function$
;

grant delete on table "public"."artifact_contents" to "anon";

grant insert on table "public"."artifact_contents" to "anon";

grant references on table "public"."artifact_contents" to "anon";

grant select on table "public"."artifact_contents" to "anon";

grant trigger on table "public"."artifact_contents" to "anon";

grant truncate on table "public"."artifact_contents" to "anon";

grant update on table "public"."artifact_contents" to "anon";

grant delete on table "public"."artifact_contents" to "authenticated";

grant insert on table "public"."artifact_contents" to "authenticated";

grant references on table "public"."artifact_contents" to "authenticated";

grant select on table "public"."artifact_contents" to "authenticated";

grant trigger on table "public"."artifact_contents" to "authenticated";

grant truncate on table "public"."artifact_contents" to "authenticated";

grant update on table "public"."artifact_contents" to "authenticated";

grant delete on table "public"."artifact_contents" to "service_role";

grant insert on table "public"."artifact_contents" to "service_role";

grant references on table "public"."artifact_contents" to "service_role";

grant select on table "public"."artifact_contents" to "service_role";

grant trigger on table "public"."artifact_contents" to "service_role";

grant truncate on table "public"."artifact_contents" to "service_role";

grant update on table "public"."artifact_contents" to "service_role";

grant delete on table "public"."artifacts_backup" to "anon";

grant insert on table "public"."artifacts_backup" to "anon";

grant references on table "public"."artifacts_backup" to "anon";

grant select on table "public"."artifacts_backup" to "anon";

grant trigger on table "public"."artifacts_backup" to "anon";

grant truncate on table "public"."artifacts_backup" to "anon";

grant update on table "public"."artifacts_backup" to "anon";

grant delete on table "public"."artifacts_backup" to "authenticated";

grant insert on table "public"."artifacts_backup" to "authenticated";

grant references on table "public"."artifacts_backup" to "authenticated";

grant select on table "public"."artifacts_backup" to "authenticated";

grant trigger on table "public"."artifacts_backup" to "authenticated";

grant truncate on table "public"."artifacts_backup" to "authenticated";

grant update on table "public"."artifacts_backup" to "authenticated";

grant delete on table "public"."artifacts_backup" to "service_role";

grant insert on table "public"."artifacts_backup" to "service_role";

grant references on table "public"."artifacts_backup" to "service_role";

grant select on table "public"."artifacts_backup" to "service_role";

grant trigger on table "public"."artifacts_backup" to "service_role";

grant truncate on table "public"."artifacts_backup" to "service_role";

grant update on table "public"."artifacts_backup" to "service_role";

create policy "Allow all users to query clusters data"
on "public"."artifact_clusters"
as permissive
for select
to authenticated
using (true);


create policy "Allow all users to query artifact_contents"
on "public"."artifact_contents"
as permissive
for select
to authenticated
using (true);


create policy "Allow all users to query artifact_domains"
on "public"."artifact_domains"
as permissive
for select
to authenticated
using (true);


create policy "Allow all users to query artifact_links"
on "public"."artifact_links"
as permissive
for select
to authenticated
using (true);


create policy "Allow all users to query artifacts"
on "public"."artifacts"
as permissive
for select
to authenticated
using (true);


create policy "Allow all users to query cluster_summaries"
on "public"."cluster_summaries"
as permissive
for select
to authenticated
using (true);



