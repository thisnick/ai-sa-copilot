set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.detect_article_clusters(target_domain_id uuid, iterations integer DEFAULT 10, resolution double precision DEFAULT 1.0)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
DECLARE
  total_edge_weight float;
BEGIN
  -- Create temporary edge table with weights, filtered by domain
  -- We now navigate via artifact_contents and unify duplicates by:
  -- 1) COALESCE for source/target
  -- 2) Adding an extra edge between artifacts and their crawled_as_artifact_id
  CREATE TEMPORARY TABLE IF NOT EXISTS temp_edges AS
  WITH consolidated_links AS (
    SELECT
      COALESCE(src_art.crawled_as_artifact_id, src_art.artifact_id) AS source_id,
      COALESCE(tgt_art.crawled_as_artifact_id, tgt_art.artifact_id) AS target_id,
      COUNT(*) AS weight
    FROM artifact_links al
    JOIN artifact_contents ac ON al.source_artifact_content_id = ac.artifact_content_id
    JOIN artifacts src_art ON ac.artifact_id = src_art.artifact_id
    JOIN artifacts tgt_art ON al.target_url = tgt_art.url
    WHERE tgt_art.domain_id = target_domain_id
    GROUP BY 1, 2
  ),
  duplicate_links AS (
    -- Treat duplicates as edges of weight 1.
    SELECT
      artifact_id AS source_id,
      crawled_as_artifact_id AS target_id,
      1 AS weight
    FROM artifacts
    WHERE crawled_as_artifact_id IS NOT NULL
  )
  SELECT * FROM consolidated_links
  UNION ALL
  SELECT * FROM duplicate_links;

  -- Get total edge weight for normalization
  SELECT SUM(weight) INTO total_edge_weight FROM temp_edges;

  -- Create temporary nodes table
  CREATE TEMPORARY TABLE IF NOT EXISTS temp_nodes AS
  SELECT
    node_id,
    node_id AS cluster_id,
    COALESCE(
      (
        SELECT SUM(weight)
        FROM temp_edges
        WHERE source_id = node_id OR target_id = node_id
      ),
      0
    ) AS degree
  FROM (
    SELECT DISTINCT COALESCE(a.crawled_as_artifact_id, a.artifact_id) AS node_id
    FROM artifacts a
    WHERE a.crawl_status = 'scraped'
      AND a.domain_id = target_domain_id
  ) sub;

  -- Create indexes
  CREATE INDEX IF NOT EXISTS idx_temp_edges_source ON temp_edges USING hash (source_id);
  CREATE INDEX IF NOT EXISTS idx_temp_edges_target ON temp_edges USING hash (target_id);
  CREATE INDEX IF NOT EXISTS idx_temp_nodes_cluster ON temp_nodes USING hash (cluster_id);

  -- Delete existing clusters for this domain
  DELETE FROM artifact_clusters
  WHERE artifact_id IN (
    SELECT DISTINCT ac.artifact_id
    FROM artifact_clusters ac
    JOIN artifacts a ON ac.artifact_id = a.artifact_id
    WHERE a.domain_id = target_domain_id
  );

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

  -- Iterate the Leiden-like algorithm
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
                n2.cluster_id AS target_cluster,
                (
                  -- K_ic: Edge weight to target cluster
                  SUM(e.weight)::float
                  -- Subtract expected edges (a_i * K_c / 2m)
                  - (n.degree::float * cs.total_degree::float / (2 * total_edge_weight))
                ) * resolution / total_edge_weight AS gain
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
                  COUNT(*) AS size,
                  SUM(degree) AS total_degree
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
        ) AS new_cluster
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
$function$
;


