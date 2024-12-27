from fastapi import FastAPI
from .serve import serve_inngest

app = FastAPI()

serve_inngest(app)


