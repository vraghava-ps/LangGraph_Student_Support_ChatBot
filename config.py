import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env or set it in the terminal.")

LLM_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"

DB_PATH = "student_support.db"

# Folder that holds the PDF knowledge base. Every *.pdf inside is indexed by the RAG node.
PDF_DIR = "data"

# Services checked by the API node. Replace the URLs with your real service health endpoints.
SERVICES = {
    "LMS Portal": "https://example.com",
    "Payment Gateway": "https://httpbin.org/status/200",
    "Video Streaming": "https://httpbin.org/status/503",  # deliberately failing, to test "down" handling
}