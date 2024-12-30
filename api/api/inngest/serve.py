import inngest.fast_api
from fastapi import FastAPI
from lib.inngest import inngest_client
# from .crawler import crawl_url, continue_crawl

def serve_inngest(app: FastAPI):
  inngest.fast_api.serve(
  app,
  inngest_client,
  # [crawl_url, continue_crawl],
  [],
  serve_path="/api/inngest",
)
