create type "public"."enum_thread_type" as enum ('runbook_generator');

drop function if exists "public"."get_top_level_clusters"(target_domain_id uuid);

create table "public"."profiles" (
    "user_id" uuid not null,
    "created_at" timestamp with time zone not null default now(),
    "name" text not null,
    "email" text not null
);


alter table "public"."profiles" enable row level security;

create table "public"."thread_states" (
    "thread_state_id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone not null default now(),
    "thread_id" uuid not null,
    "messages" jsonb not null,
    "context_variables" jsonb not null,
    "agent_name" text
);


alter table "public"."thread_states" enable row level security;

create table "public"."threads" (
    "thread_id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone not null default now(),
    "user_id" uuid not null,
    "last_known_good_thread_state_id" uuid,
    "thread_type" enum_thread_type not null,
    "title" text
);


alter table "public"."threads" enable row level security;

CREATE UNIQUE INDEX profiles_pkey ON public.profiles USING btree (user_id);

CREATE UNIQUE INDEX thread_states_pkey ON public.thread_states USING btree (thread_state_id);

CREATE INDEX thread_states_thread_id_idx ON public.thread_states USING btree (thread_id);

CREATE UNIQUE INDEX threads_pkey ON public.threads USING btree (thread_id);

CREATE INDEX threads_user_id_thread_type_idx ON public.threads USING btree (user_id, thread_type);

alter table "public"."profiles" add constraint "profiles_pkey" PRIMARY KEY using index "profiles_pkey";

alter table "public"."thread_states" add constraint "thread_states_pkey" PRIMARY KEY using index "thread_states_pkey";

alter table "public"."threads" add constraint "threads_pkey" PRIMARY KEY using index "threads_pkey";

alter table "public"."profiles" add constraint "profiles_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."profiles" validate constraint "profiles_user_id_fkey";

alter table "public"."thread_states" add constraint "thread_states_thread_id_fkey" FOREIGN KEY (thread_id) REFERENCES threads(thread_id) ON DELETE CASCADE not valid;

alter table "public"."thread_states" validate constraint "thread_states_thread_id_fkey";

alter table "public"."threads" add constraint "threads_last_known_good_thread_state_id_fkey" FOREIGN KEY (last_known_good_thread_state_id) REFERENCES thread_states(thread_state_id) ON DELETE SET NULL not valid;

alter table "public"."threads" validate constraint "threads_last_known_good_thread_state_id_fkey";

alter table "public"."threads" add constraint "threads_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(user_id) ON DELETE CASCADE not valid;

alter table "public"."threads" validate constraint "threads_user_id_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.create_profile()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  INSERT INTO profiles (user_id, name, email)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data ->> 'name',
    NEW.raw_user_meta_data ->> 'email'
  );
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_artifacts_with_links(artifact_ids uuid[], max_links integer DEFAULT 10)
 RETURNS TABLE(artifact_id uuid, url text, title text, summary text, parsed_text text, outbound_links jsonb, inbound_links jsonb)
 LANGUAGE plpgsql
AS $function$ BEGIN RETURN QUERY
SELECT a.artifact_id,
    a.url,
    a.title,
    a.summary,
    a.parsed_text,
    COALESCE(
        (
            SELECT jsonb_agg(outbound)
            FROM (
                    SELECT DISTINCT ON (al.target_url) jsonb_build_object(
                            'artifact_id',
                            target.artifact_id,
                            'url',
                            target.url,
                            'title',
                            target.title,
                            'summary',
                            target.summary
                        ) AS outbound
                    FROM artifact_links al
                        LEFT JOIN artifacts target ON al.target_url = target.url
                    WHERE al.source_artifact_id = a.artifact_id
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
                    SELECT DISTINCT ON (il.source_artifact_id) jsonb_build_object(
                            'artifact_id',
                            il.source_artifact_id,
                            'url',
                            source.url,
                            'title',
                            source.title,
                            'summary',
                            source.summary
                        ) AS inbound
                    FROM artifact_links il
                        LEFT JOIN artifacts source ON il.source_artifact_id = source.artifact_id
                    WHERE il.target_url = a.url
                    ORDER BY il.source_artifact_id
                    LIMIT max_links
                ) AS inbound_links
        ),
        '[]'::jsonb
    ) AS inbound_links
FROM artifacts a
WHERE a.artifact_id = ANY(artifact_ids);
END;
$function$
;

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

grant delete on table "public"."profiles" to "anon";

grant insert on table "public"."profiles" to "anon";

grant references on table "public"."profiles" to "anon";

grant select on table "public"."profiles" to "anon";

grant trigger on table "public"."profiles" to "anon";

grant truncate on table "public"."profiles" to "anon";

grant update on table "public"."profiles" to "anon";

grant delete on table "public"."profiles" to "authenticated";

grant insert on table "public"."profiles" to "authenticated";

grant references on table "public"."profiles" to "authenticated";

grant select on table "public"."profiles" to "authenticated";

grant trigger on table "public"."profiles" to "authenticated";

grant truncate on table "public"."profiles" to "authenticated";

grant update on table "public"."profiles" to "authenticated";

grant delete on table "public"."profiles" to "service_role";

grant insert on table "public"."profiles" to "service_role";

grant references on table "public"."profiles" to "service_role";

grant select on table "public"."profiles" to "service_role";

grant trigger on table "public"."profiles" to "service_role";

grant truncate on table "public"."profiles" to "service_role";

grant update on table "public"."profiles" to "service_role";

grant delete on table "public"."thread_states" to "anon";

grant insert on table "public"."thread_states" to "anon";

grant references on table "public"."thread_states" to "anon";

grant select on table "public"."thread_states" to "anon";

grant trigger on table "public"."thread_states" to "anon";

grant truncate on table "public"."thread_states" to "anon";

grant update on table "public"."thread_states" to "anon";

grant delete on table "public"."thread_states" to "authenticated";

grant insert on table "public"."thread_states" to "authenticated";

grant references on table "public"."thread_states" to "authenticated";

grant select on table "public"."thread_states" to "authenticated";

grant trigger on table "public"."thread_states" to "authenticated";

grant truncate on table "public"."thread_states" to "authenticated";

grant update on table "public"."thread_states" to "authenticated";

grant delete on table "public"."thread_states" to "service_role";

grant insert on table "public"."thread_states" to "service_role";

grant references on table "public"."thread_states" to "service_role";

grant select on table "public"."thread_states" to "service_role";

grant trigger on table "public"."thread_states" to "service_role";

grant truncate on table "public"."thread_states" to "service_role";

grant update on table "public"."thread_states" to "service_role";

grant delete on table "public"."threads" to "anon";

grant insert on table "public"."threads" to "anon";

grant references on table "public"."threads" to "anon";

grant select on table "public"."threads" to "anon";

grant trigger on table "public"."threads" to "anon";

grant truncate on table "public"."threads" to "anon";

grant update on table "public"."threads" to "anon";

grant delete on table "public"."threads" to "authenticated";

grant insert on table "public"."threads" to "authenticated";

grant references on table "public"."threads" to "authenticated";

grant select on table "public"."threads" to "authenticated";

grant trigger on table "public"."threads" to "authenticated";

grant truncate on table "public"."threads" to "authenticated";

grant update on table "public"."threads" to "authenticated";

grant delete on table "public"."threads" to "service_role";

grant insert on table "public"."threads" to "service_role";

grant references on table "public"."threads" to "service_role";

grant select on table "public"."threads" to "service_role";

grant trigger on table "public"."threads" to "service_role";

grant truncate on table "public"."threads" to "service_role";

grant update on table "public"."threads" to "service_role";

create policy "Allow all users to access clusters"
on "public"."artifact_clusters"
as permissive
for all
to public
using (true)
with check (true);


create policy "Allow all users to access summaries"
on "public"."cluster_summaries"
as permissive
for all
to public
using (true)
with check (true);


create policy "Allow users to access their own profiles"
on "public"."profiles"
as permissive
for all
to authenticated
using ((( SELECT auth.uid() AS uid) = user_id))
with check ((( SELECT auth.uid() AS uid) = user_id));


create policy "Users can access their own thread states"
on "public"."thread_states"
as permissive
for all
to authenticated
using ((( SELECT auth.uid() AS uid) IN ( SELECT threads.user_id
   FROM threads
  WHERE (threads.thread_id = thread_states.thread_id))))
with check ((( SELECT auth.uid() AS uid) IN ( SELECT threads.user_id
   FROM threads
  WHERE (threads.thread_id = thread_states.thread_id))));


create policy "Users can access their own threads"
on "public"."threads"
as permissive
for all
to authenticated
using ((( SELECT auth.uid() AS uid) = user_id))
with check ((( SELECT auth.uid() AS uid) = user_id));



