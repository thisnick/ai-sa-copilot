"use server"

import { createClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";

export async function getChatHistory(page: number = 1, pageSize: number = 10) {
  const supabase = await createClient();
  const { data: { user }, error } = await supabase.auth.getUser();

  if (!user) {
    throw new Error("Please login to view chat history");
  }

  const { data: threads, error: threadStateError } = await supabase
    .from("threads")
    .select("*")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false })
    .range((page - 1) * pageSize, page * pageSize - 1);

  if (threadStateError) {
    throw new Error("Failed to fetch chat history");
  }
  return threads;
}

export async function deleteThread(threadId: string) {
  const supabase = await createClient();
  const { data: { user }, error } = await supabase.auth.getUser();

  if (!user) {
    throw new Error("Please login to view chat history");
  }

  const { error: deleteError } = await supabase
    .from("threads")
    .delete()
    .eq("thread_id", threadId)
    .eq("user_id", user.id);

  if (deleteError) {
    throw new Error("Failed to delete thread");
  }

  return { deleted: true };
}
