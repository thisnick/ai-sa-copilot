set check_function_bodies = off;

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
           INNER JOIN artifacts target ON al.target_url = target.url AND target.domain_id = a.domain_id
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
           INNER JOIN artifact_contents source_content ON il.source_artifact_content_id = source_content.artifact_content_id
           INNER JOIN artifacts source_artifact ON source_content.artifact_id = source_artifact.artifact_id
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


