import inngest.fast_api
from fastapi import FastAPI
from lib.inngest import inngest_client
from .crawl_url import crawl_url
from .resume_crawl import resume_crawl
from .cluster_artifacts import cluster_artifacts
from .copy_to_naive_domain import copy_to_naive_domain

def serve_inngest(app: FastAPI):
  inngest.fast_api.serve(
  app,
  inngest_client,
  [crawl_url, resume_crawl, cluster_artifacts, copy_to_naive_domain],
  serve_path="/api/inngest",
)
