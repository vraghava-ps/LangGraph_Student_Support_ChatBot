import streamlit as st

from graph import graph

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Student Support Chatbot", page_icon="🎓", layout="centered")

ROUTE_LABELS = {
    "payment": "💳 Database Node (Payments)",
    "course": "📚 RAG Node (Courses)",
    "api_status": "🛰️ API Node (Service Status)",
    "general": "💬 General Node",
}

SAMPLE_QUESTIONS = [
    "What is the pending fee for STU1001?",
    "What are the prerequisites for the DevOps bootcamp?",
    "Is the video streaming service down?",
    "Hi, what can you help me with?",
]

# ---------------------------------------------------------------------------
# Session state (chat history survives Streamlit reruns)
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("About")
    st.write(
        "Ask about **payments**, **courses**, **service status**, or anything general. "
        "The classifier routes each question to the right node."
    )
    st.caption("For payment questions, include your student ID, e.g. STU1001.")

    st.subheader("Try a sample")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pop("pending_question", None)
        st.rerun()

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("🎓 Student Support Chatbot")
st.caption("Powered by LangGraph + OpenAI")

# Replay previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("category"):
            st.caption(f"Routed to: {ROUTE_LABELS.get(msg['category'], msg['category'])}")

# Input: typed question or a sample button click
typed = st.chat_input("Type your question here...")
question = typed or st.session_state.pop("pending_question", None)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = graph.invoke({"question": question})
                answer = result["answer"]
                category = result["category"]
            except Exception as e:
                answer = f"Sorry, something went wrong: {e}"
                category = None

        st.markdown(answer)
        if category:
            st.caption(f"Routed to: {ROUTE_LABELS.get(category, category)}")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "category": category}
    )