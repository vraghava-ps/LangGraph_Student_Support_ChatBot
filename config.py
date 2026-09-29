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

# ---------------------------------------------------------------------------
# Institute details (used by the General node and the Answer node)
# ---------------------------------------------------------------------------
INSTITUTE_NAME = "PSG IT Solutions"

INSTITUTE_PROFILE = f"""Institute name: {INSTITUTE_NAME}
{INSTITUTE_NAME} is a technology training institute offering job-oriented courses: DevOps with AWS,
DevOps with Azure, DevOps with GCP, Python Programming, Generative AI, Agentic AI with LangGraph,
Data Science with Python, Docker and Kubernetes, Terraform, Linux and Shell Scripting, and
Full Stack Development with Python. More courses are added regularly.
Learning modes: live online classes and classroom batches, with recordings on the LMS.
This assistant can help with: payment status of a student (share the student ID, e.g. STU1001),
course details and policies (including the refund policy), and the live status of the LMS Portal,
Payment Gateway and Video Streaming services.
Support hours: Monday to Saturday, 9:30 AM to 6:30 PM IST."""

# Services checked by the API node. Replace the URLs with your real service health endpoints.
SERVICES = {
    "LMS Portal": "https://example.com",
    "Payment Gateway": "https://httpbin.org/status/200",
    "Video Streaming": "https://httpbin.org/status/503",  # deliberately failing, to test "down" handling
}