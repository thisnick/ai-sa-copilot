alter table "public"."artifacts" add column "content_sha256" text;

alter table "public"."artifacts" add column "crawled_as_artifact_id" uuid;

CREATE UNIQUE INDEX artifact_contents_artifact_id_anchor_id_key ON public.artifact_contents USING btree (artifact_id, anchor_id);

CREATE INDEX artifacts_content_sha256_idx ON public.artifacts USING btree (content_sha256);

alter table "public"."artifact_contents" add constraint "artifact_contents_artifact_id_anchor_id_key" UNIQUE using index "artifact_contents_artifact_id_anchor_id_key";

alter table "public"."artifacts" add constraint "artifacts_crawled_as_artifact_id_fkey" FOREIGN KEY (crawled_as_artifact_id) REFERENCES artifacts(artifact_id) ON DELETE SET NULL not valid;

alter table "public"."artifacts" validate constraint "artifacts_crawled_as_artifact_id_fkey";


