import re
import sqlite3
from pathlib import Path
from typing import Literal

import requests
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from pypdf import PdfReader

from config import DB_PATH, EMBED_MODEL, LLM_MODEL, PDF_DIR, SERVICES
from state import ChatState

llm = ChatOpenAI(model=LLM_MODEL, temperature=0)


# ---------------------------------------------------------------------------
# 1. CLASSIFIER NODE
# ---------------------------------------------------------------------------
class Classification(BaseModel):
    category: Literal["payment", "course", "api_status", "general"] = Field(
        description="The single best category for the student's question."
    )


CLASSIFIER_PROMPT = """You classify student-support questions for PSG IT Solutions into exactly one category.

Categories:

payment
  Questions about the student's OWN personal payment records: their pending dues,
  payment status, failed transactions, paid amount, due dates, or invoice for their account.
  Usually mentions "my payment", "my fee", "my due", or a student ID like STU1001.

course
  Questions about courses and institute rules that apply to everyone: the list of courses offered,
  syllabus, duration, course fees, prerequisites, batches, certificates, attendance rules,
  batch switching, recorded sessions, placement support, contact details, and ALL POLICIES,
  including the refund policy and refund eligibility.
  Anything that would be answered from the institute's handbook or documents is "course".

api_status
  Questions about whether a service, portal, website, platform or API is down, slow,
  not loading, or working (LMS portal, payment gateway, video streaming).

general
  Greetings, small talk, and anything that fits none of the above.

Important rules:
- A question about a POLICY or RULE (for example "What is the refund policy?") is "course",
  even if it mentions money words like refund, fee or payment.
- Only choose "payment" when the student wants to know about THEIR OWN account or transaction.

Examples:
- "What courses do you offer?" -> course
- "What is the fee for DevOps with Azure?" -> course
- "What is the refund policy?" -> course
- "How many days do I have to ask for a refund?" -> course
- "What is the pending fee for STU1001?" -> payment
- "Why did my payment fail? My ID is STU1002" -> payment
- "Has my refund been processed? My ID is STU1002" -> payment
- "Is the payment gateway down?" -> api_status
- "LMS is not loading" -> api_status
- "Hi, who are you?" -> general
"""

classifier_llm = llm.with_structured_output(Classification)


def classifier_node(state: ChatState) -> dict:
    result = classifier_llm.invoke(
        [
            SystemMessage(content=CLASSIFIER_PROMPT),
            HumanMessage(content=state["question"]),
        ]
    )
    return {"category": result.category}


def route_by_category(state: ChatState) -> str:
    """Used by the conditional edge; returns the category which graph.py maps to a node."""
    return state["category"]


# ---------------------------------------------------------------------------
# 2. DATABASE NODE  (payment questions)
# ---------------------------------------------------------------------------
def database_node(state: ChatState) -> dict:
    match = re.search(r"STU\d+", state["question"], re.IGNORECASE)
    if not match:
        return {
            "context": "No student ID was provided. Ask the student to share their student ID (format: STU1234) "
                       "so their payment records can be looked up."
        }

    student_id = match.group(0).upper()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT course, amount, status, due_date, paid_on FROM payments WHERE student_id = ?",
        (student_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return {"context": f"No payment records found for student ID {student_id}."}

    lines = [
        f"- {r['course']}: amount {r['amount']} INR, status {r['status']}, "
        f"due {r['due_date']}, paid on {r['paid_on'] or 'N/A'}"
        for r in rows
    ]
    return {"context": f"Payment records for {student_id}:\n" + "\n".join(lines)}


# ---------------------------------------------------------------------------
# 3. RAG NODE  (course questions, answered from PDF files)
# ---------------------------------------------------------------------------
_vector_store = None


def _load_pdf_documents(pdf_dir: str) -> list[Document]:
    """Read every PDF in the folder, one Document per page (keeps file name + page number)."""
    pdf_files = sorted(Path(pdf_dir).glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in '{pdf_dir}/'. Add at least one PDF and restart the app."
        )

    documents = []
    for pdf_path in pdf_files:
        reader = PdfReader(str(pdf_path))
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"source": pdf_path.name, "page": page_number},
                    )
                )

    if not documents:
        raise ValueError(
            "The PDF files contain no extractable text. They may be scanned images. "
            "Use a text-based PDF or run OCR on it first."
        )
    return documents


def _get_vector_store() -> InMemoryVectorStore:
    """Build the vector store once, on first use."""
    global _vector_store
    if _vector_store is None:
        pages = _load_pdf_documents(PDF_DIR)
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(pages)  # metadata is carried over to each chunk
        _vector_store = InMemoryVectorStore.from_documents(
            chunks, embedding=OpenAIEmbeddings(model=EMBED_MODEL)
        )
    return _vector_store


def rag_node(state: ChatState) -> dict:
    docs = _get_vector_store().similarity_search(state["question"], k=5)
    parts = [
        f"[Source: {d.metadata['source']}, page {d.metadata['page']}]\n{d.page_content}"
        for d in docs
    ]
    return {"context": "Relevant information from the documents:\n\n" + "\n\n".join(parts)}


# ---------------------------------------------------------------------------
# 4. API NODE  (service-status questions)
# ---------------------------------------------------------------------------
def api_node(state: ChatState) -> dict:
    results = []
    for name, url in SERVICES.items():
        try:
            resp = requests.get(url, timeout=5)
            status = "UP" if resp.status_code < 400 else f"DEGRADED (HTTP {resp.status_code})"
        except requests.RequestException:
            status = "DOWN (unreachable)"
        results.append(f"- {name}: {status}")
    return {"context": "Live service status:\n" + "\n".join(results)}


# ---------------------------------------------------------------------------
# 5. GENERAL NODE
# ---------------------------------------------------------------------------
def general_node(state: ChatState) -> dict:
    return {
        "context": "This is a general question. No database, document or service data is attached. "
                   "Answer helpfully and briefly. For account-specific issues, suggest contacting the support team."
    }


# ---------------------------------------------------------------------------
# 6. ANSWER NODE
# ---------------------------------------------------------------------------
ANSWER_PROMPT = """You are the friendly student-support assistant for PSG IT Solutions.
Answer the student's question using ONLY the context provided when it is relevant.
If the context comes from documents, mention the source file and page number at the end, like (Source: file.pdf, page 2).
If the context does not contain the answer, say so honestly and suggest contacting the support team.
Keep the answer clear and concise."""


def answer_node(state: ChatState) -> dict:
    response = llm.invoke(
        [
            SystemMessage(content=ANSWER_PROMPT),
            HumanMessage(
                content=f"Question: {state['question']}\n\nContext:\n{state.get('context', '')}"
            ),
        ]
    )
    return {"answer": response.content}