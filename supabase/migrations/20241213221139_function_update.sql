set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.get_top_level_clusters(target_domain_id uuid)
 RETURNS TABLE(cluster_id uuid, member_count integer, iteration integer, summary jsonb)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        ac.cluster_id,
        cs.member_count,
        ac.iteration,
        cs.summary
    FROM 
        public.artifact_clusters ac
    JOIN 
        public.artifacts a ON ac.cluster_id = a.artifact_id
    LEFT OUTER JOIN 
        public.cluster_summaries cs ON ac.cluster_id = cs.cluster_id AND ac.iteration = cs.iteration
    WHERE 
        a.domain_id = target_domain_id
        AND ac.is_intermediate = false
    ORDER BY 
        member_count DESC;
END;
$function$
;


