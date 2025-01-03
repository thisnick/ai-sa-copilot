'use server';

import { convertToUIMessages } from "@/lib/api/utils";
import { createClient } from "@/lib/supabase/server";
import type { DBMessage, ContextVariables } from "@/lib/api/types";
import { Tables } from "@/lib/supabase/database.types";
import { notFound } from "next/navigation";
import { cookies } from 'next/headers';

export async function saveDomainId(domainId: string) {
  const cookieStore = await cookies();
  cookieStore.set('domain-id', domainId);
}

export async function getThreadState(threadId: string) {
  const supabase = await createClient();
  const { data: { user }, error } = await supabase.auth.getUser();

  if (!user) {
    throw new Error("User not found");
  }

  const { data: thread, error: threadStateError } = await supabase
    .from("threads")
    .select("*, state:thread_states!last_known_good_thread_state_id(*)")
    .eq("thread_id", threadId)
    .eq("user_id", user.id)
    .limit(1)
    .maybeSingle();

  if (threadStateError) {
    return notFound();
  }

  if (!thread) {
    return null;
  }

  const threadState = thread.state as unknown as Tables<'thread_states'>;

  const messages = convertToUIMessages(threadState?.messages as Array<DBMessage> || []);

  const context = threadState.context_variables as ContextVariables;

  return {
    messages,
    context,
  };
}
