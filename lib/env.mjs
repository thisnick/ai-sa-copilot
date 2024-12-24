import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";
import "dotenv/config";

export const env = createEnv({
  server: {
    NODE_ENV: z
      .enum(["development", "test", "production"])
      .default("development"),
    OPENAI_API_KEY: z.string().default(""),
    SUPABASE_SERVICE_ROLE_KEY: z.string().default(""),
    VERCEL_ENV: z.string().default("development"),
    GROQ_API_KEY: z.string().default(""),
    AGENT_LLM_MODEL: z.string().default(""),
    NOMIC_API_KEY: z.string().default(""),
  },
  client: {
    NEXT_PUBLIC_SUPABASE_URL: z.string().default(""),
    NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().default(""),
  },
  runtimeEnv: {
    NODE_ENV: process.env.NODE_ENV,
    DATABASE_URL: process.env.DATABASE_URL,
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
    SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,
    VERCEL_ENV: process.env.VERCEL_ENV,
    GROQ_API_KEY: process.env.GROQ_API_KEY,
    AGENT_LLM_MODEL: process.env.AGENT_LLM_MODEL,
    NOMIC_API_KEY: process.env.NOMIC_API_KEY,
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  },
});
