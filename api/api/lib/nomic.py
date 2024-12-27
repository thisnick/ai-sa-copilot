from typing import List, Literal, Optional
from pydantic import BaseModel
import aiohttp
import json

TaskType = Literal["search_document", "search_query", "classification", "clustering"]
LongTextMode = Literal["truncate", "mean"]
ModelType = Literal["nomic-embed-text-v1", "nomic-embed-text-v1.5"]

class EmbeddingUsage(BaseModel):
  prompt_tokens: int
  total_tokens: int

class NomicEmbeddingResult(BaseModel):
  embeddings: List[List[float]]
  usage: EmbeddingUsage
  model: Literal["nomic-embed-text-v1", "nomic-embed-text-v1.5"]

class NomicEmbeddings:
  def __init__(
    self,
    api_key: str,
    base_url: str = "https://api-atlas.nomic.ai/",
  ):
    self.api_key = api_key
    self.base_url = base_url.rstrip('/')
    self.headers = {
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/json",
    }

  async def embed_texts(
    self,
    texts: List[str],
    model: ModelType = "nomic-embed-text-v1.5",
    task_type: TaskType = "search_document",
    long_text_mode: LongTextMode = "truncate",
    max_tokens_per_text: int = 8192,
    dimensionality: Optional[Literal[768, 512, 256, 128, 64]] = 768,
  ) -> NomicEmbeddingResult:
    """Generate embeddings for a list of texts using Nomic's API."""

    payload = {
      "texts": texts,
      "model": model,
      "task_type": task_type,
      "long_text_mode": long_text_mode,
      "max_tokens_per_text": max_tokens_per_text,
      "dimensionality": dimensionality,
    }

    async with aiohttp.ClientSession() as session:
      async with session.post(
        f"{self.base_url}/v1/embedding/text",
        headers=self.headers,
        json=payload
      ) as response:
        if response.status != 200:
          error_text = await response.text()
          raise Exception(f"API request failed with status {response.status}: {error_text}")

        result = await response.json()
        return NomicEmbeddingResult.model_validate(result)
