import logging
import inngest

from ..config import Settings

settings = Settings()

# Create an Inngest client
inngest_client = inngest.Inngest(
  app_id=settings.vercel_env == "production" and "ai-sdk-preview-rag" or "ai-sdk-preview-rag-dev",
  logger=logging.getLogger("uvicorn"),
  is_production=settings.vercel_env in ["production", "preview"],
)

