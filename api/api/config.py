from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  openai_api_key: str = ""
  next_public_supabase_url: str = ""
  next_public_supabase_anon_key: str = ""
  supabase_service_role_key: str = ""
  vercel_env: str = "development"
  groq_api_key: str = ""
  agent_llm_model: str = ""
  nomic_api_key: str = ""

  model_config = SettingsConfigDict(env_file=".env", extra="allow")

