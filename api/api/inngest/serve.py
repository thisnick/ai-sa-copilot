import inngest.fast_api
from fastapi import FastAPI
from lib.inngest import inngest_client
from .crawl_url import crawl_url
from .resume_crawl import resume_crawl

def serve_inngest(app: FastAPI):
  inngest.fast_api.serve(
  app,
  inngest_client,
  [crawl_url, resume_crawl],
  serve_path="/api/inngest",
)
