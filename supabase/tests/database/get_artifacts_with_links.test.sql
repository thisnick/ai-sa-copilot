begin;
select plan(5);

-- 1. Insert two domains
insert into public.artifact_domains (id, name, config, visibility)
values
  ('00000000-0000-0000-0000-000000000001', 'Test Domain A', '{}', 'public'),
  ('00000000-0000-0000-0000-000000000002', 'Test Domain B', '{}', 'public');

-- 2. Insert artifacts for each domain
insert into public.artifacts (
  artifact_id, url, domain_id, crawl_depth, crawl_status
) values
  -- Domain A artifacts
  ('11111111-1111-1111-1111-111111111111', 'https://example.com/a1', '00000000-0000-0000-0000-000000000001', 0, 'scraped'),
  ('11111111-1111-1111-1111-222222222222', 'https://example.com/a2', '00000000-0000-0000-0000-000000000001', 0, 'scraped'),
  -- Domain B artifact
  ('22222222-2222-2222-2222-333333333333', 'https://otherdomain.com/b1', '00000000-0000-0000-0000-000000000002', 0, 'scraped');

-- 3. Insert artifact_contents for each artifact
insert into public.artifact_contents (
  artifact_content_id, artifact_id, parsed_text, title, summary_embedding, summary
) values
  -- Domain A content
  ('aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1', '11111111-1111-1111-1111-111111111111', 'Content for a1', 'Title A1', (SELECT array_fill(0.0, ARRAY[768])::vector(768)), 'Summary A1'),
  ('aaaaaaa2-aaaa-aaaa-aaaa-aaaaaaaaaaa2', '11111111-1111-1111-1111-222222222222', 'Content for a2', 'Title A2', (SELECT array_fill(0.0, ARRAY[768])::vector(768)), 'Summary A2'),
  -- Domain B content
  ('bbbbbbb1-bbbb-bbbb-bbbb-bbbbbbbbbbb1', '22222222-2222-2222-2222-333333333333', 'Content for b1', 'Title B1', (SELECT array_fill(0.0, ARRAY[768])::vector(768)), 'Summary B1');

-- 4. Insert links
-- 4a. Valid link: A1 -> A2
insert into public.artifact_links (id, source_artifact_content_id, anchor_text, target_url) values
  ('10000001-0000-0000-0000-000000000001', 'aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1', 'link A1->A2', 'https://example.com/a2');

-- 4b. Invalid link: A2 -> invalid (no artifact with this URL in Domain A)
insert into public.artifact_links (id, source_artifact_content_id, anchor_text, target_url) values
  ('20000002-0000-0000-0000-000000000002', 'aaaaaaa2-aaaa-aaaa-aaaa-aaaaaaaaaaa2', 'link A2->Missing', 'https://example.com/does-not-exist');

-- 4c. Cross-domain link: A1 -> B1 (this should not appear in the returned outbound links since B1's domain doesn't match Domain A)
insert into public.artifact_links (id, source_artifact_content_id, anchor_text, target_url) values
  ('30000003-0000-0000-0000-000000000003', 'aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1', 'Cross A->B', 'https://otherdomain.com/b1');

-- We will test the function get_artifacts_with_links with artifact_content_ids from Domain A
-- 5. Check that we get 2 results back for the array of both content IDs in Domain A
select is(
  (select count(*)::integer from public.get_artifacts_with_links(
     array['aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1','aaaaaaa2-aaaa-aaaa-aaaa-aaaaaaaaaaa2']::uuid[], 10
  )),
  2,
  'Should return 2 rows (for each artifact_content_id in Domain A).'
);

-- 6. Check that the outbound_links for A1 includes exactly 1 valid link (A2)
--    and excludes the invalid link and cross-domain link
select is(
  (select jsonb_array_length(outbound_links)
   from public.get_artifacts_with_links(
     array['aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1']::uuid[], 10
   )
   limit 1),
  1,
  'A1 should have exactly 1 valid outbound link (A2).'
);

-- 7. Check that A2 has 0 valid outbound links
select is(
  (select jsonb_array_length(outbound_links)
   from public.get_artifacts_with_links(
     array['aaaaaaa2-aaaa-aaaa-aaaa-aaaaaaaaaaa2']::uuid[], 10
   )
   limit 1),
  0,
  'A2 should have 0 valid outbound links (target_url did not match any domain A artifact).'
);

-- 8. Verify that no results are returned for content id in Domain B if not queried
select is(
  (select count(*)::integer
   from public.get_artifacts_with_links(
     array['bbbbbbb1-bbbb-bbbb-bbbb-bbbbbbbbbbb1']::uuid[], 10
   )),
  1,
  'Just confirming B1 is returned if we query its own content ID...'
);

-- 9. Verify that inbound_links for B1 do not include A1 references,
--    because the function excludes cross-domain link for inbound
select is(
  (select jsonb_array_length(inbound_links)
   from public.get_artifacts_with_links(
     array['bbbbbbb1-bbbb-bbbb-bbbb-bbbbbbbbbbb1']::uuid[], 10
   )
   limit 1),
  0,
  'B1 should have 0 inbound links from Domain A artifact content.'
);

select * from finish();
rollback;
