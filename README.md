# Student Support Chatbot

A LangGraph-based student support chatbot that classifies each question and routes it to the right node.

## Flow

START → Classifier → (Database | RAG | API | General) → Answer → END

| Category | Node | Source |
|---|---|---|
| Payment | Database | SQLite `payments` table |
| Course | RAG | PDF files in `data/` + OpenAI embeddings |
| API/Service status | API | Live HTTP health checks |
| General | General | LLM |

## Tech Stack
Python, LangGraph, LangChain, OpenAI (gpt-4o-mini, text-embedding-3-small), SQLite

## Setup (Windows CMD)

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```env
OPENAI_API_KEY=your-key-here
```

Seed the database and run:

```cmd
python init_db.py
python main.py
```

## Sample Questions
- What is the pending fee for STU1001?
- What are the prerequisites for the DevOps bootcamp?
- Is the payment gateway down?
- Hi, what can you help me with?

## Project Structure
- `config.py`: settings and service URLs
- `state.py`: shared graph state
- `nodes.py`: classifier, database, RAG, API, general and answer nodes
- `graph.py`: LangGraph wiring
- `main.py`: CLI chat loop
- `init_db.py`: creates and seeds sample data
- `data/`: PDF documents used by the RAG node


## Knowledge base
Place one or more text-based PDF files in the `data/` folder. The RAG node indexes every PDF
and cites the file name and page number in its answers.