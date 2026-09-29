from typing import TypedDict


class ChatState(TypedDict, total=False):
    question: str   # the student's question
    category: str   # payment | course | api_status | general
    context: str    # data gathered by the DB / RAG / API / General node
    answer: str     # final response