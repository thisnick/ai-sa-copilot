import { embed, embedMany } from "ai";
import { cosineDistance, desc, gt, sql } from "drizzle-orm";
import NomicTextEmbedding from "./nomic-text-embedding";
import { createClient } from "../supabase/server";

const embeddingModel = new NomicTextEmbedding({ taskType: "search_query" });

const generateChunks = (input: string): string[] => {
  return input
    .trim()
    .split(".")
    .filter((i) => i !== "");
};

export const generateEmbeddings = async (
  value: string,
): Promise<Array<{ embedding: number[]; content: string }>> => {
  const chunks = generateChunks(value);
  const { embeddings } = await embedMany({
    model: embeddingModel,
    values: chunks,
  });
  return embeddings.map((e, i) => ({ content: chunks[i], embedding: e }));
};

export const generateEmbedding = async (value: string): Promise<number[]> => {
  const input = value.replaceAll("\n", " ");
  const { embedding } = await embed({
    model: embeddingModel,
    value: input,
  });
  return embedding;
};

export const findRelevantContent = async (userQuery: string) => {
  const userQueryEmbedded = await generateEmbedding(userQuery);
  const supabase = await createClient();
  const { data, error } = await supabase.rpc("match_artifacts", {
    query_embedding: JSON.stringify(userQueryEmbedded),
    match_count: 4,
    filter: {},
  });
  if (error) {
    throw Error(error.message);
  }
  const filteredData = data.filter((d) => d.similarity > 0.3);

  return filteredData;
};
