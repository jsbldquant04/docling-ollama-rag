import os
import tempfile
import uuid

import streamlit as st

from src.document_processor import process_pdf
from src.rag import answer_question
from src.vector_store import SessionVectorStore

st.set_page_config(
    page_title="PaperLens AI",
    page_icon="📚",
    layout="wide",
)

st.title("📚 PaperLens AI")
st.caption("Chat with research papers and financial reports using Docling + RAG.")

with st.sidebar:
    st.header("How it works")
    st.markdown(
        """
        1. Upload a PDF.
        2. Docling reads its structure.
        3. The document is split into meaningful chunks.
        4. Local embeddings index the chunks.
        5. Your question retrieves relevant passages.
        6. The LLM answers from those passages.
        """
    )
    st.divider()
    st.info(
        "Public-demo design: uploaded PDFs and vectors are kept only in your "
        "current Streamlit session. Do not upload confidential documents."
    )

def get_api_key():
    # Streamlit Cloud secrets first; .env/environment variables second.
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return os.getenv("OPENAI_API_KEY")

def get_model():
    try:
        return st.secrets.get("LLM_MODEL", "gpt-5-mini")
    except Exception:
        return os.getenv("LLM_MODEL", "gpt-5-mini")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "vector_store" not in st.session_state:
    st.session_state.vector_store = SessionVectorStore()

if "document_name" not in st.session_state:
    st.session_state.document_name = None

if "document_fingerprint" not in st.session_state:
    st.session_state.document_fingerprint = None

uploaded_file = st.file_uploader(
    "Upload a research paper or financial report",
    type=["pdf"],
    help="PDF only. For this demo, keep documents reasonably sized.",
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    fingerprint = f"{uploaded_file.name}:{len(file_bytes)}:{hash(file_bytes)}"

    if fingerprint != st.session_state.document_fingerprint:
        with st.status("Reading and indexing your PDF...", expanded=True) as status:
            st.write("Parsing the document with Docling...")
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                chunks = process_pdf(tmp_path, uploaded_file.name)
                st.write(f"Created {len(chunks)} searchable chunks.")

                st.write("Creating embeddings and building your session index...")
                st.session_state.vector_store = SessionVectorStore()
                st.session_state.vector_store.add_chunks(chunks)

                st.session_state.document_name = uploaded_file.name
                st.session_state.document_fingerprint = fingerprint
                st.session_state.messages = []
                status.update(label="PDF ready — ask a question!", state="complete")
            except Exception as exc:
                status.update(label="PDF processing failed", state="error")
                st.error(f"Could not process this PDF: {exc}")
            finally:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

if st.session_state.document_name:
    st.success(f"Ready: **{st.session_state.document_name}**")

    if st.button("Clear document and chat"):
        st.session_state.vector_store = SessionVectorStore()
        st.session_state.document_name = None
        st.session_state.document_fingerprint = None
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Retrieved sources"):
                for source in message["sources"]:
                    st.markdown(
                        f"- **{source['source']}** — chunk {source['chunk_id']} "
                        f"(similarity {source['score']:.3f})"
                    )

question = st.chat_input(
    "Ask about the uploaded document...",
    disabled=not bool(st.session_state.document_name),
)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        api_key = get_api_key()
        if not api_key:
            answer = (
                "The app owner has not configured `OPENAI_API_KEY`. "
                "Add it to `.streamlit/secrets.toml` locally or Streamlit "
                "Community Cloud Secrets when deployed."
            )
            sources = []
            st.error(answer)
        else:
            with st.spinner("Searching the document and generating an answer..."):
                result = answer_question(
                    question=question,
                    vector_store=st.session_state.vector_store,
                    api_key=api_key,
                    model=get_model(),
                )
            answer = result["answer"]
            sources = result["sources"]
            st.markdown(answer)

            with st.expander("Retrieved sources"):
                for source in sources:
                    st.markdown(
                        f"- **{source['source']}** — chunk {source['chunk_id']} "
                        f"(similarity {source['score']:.3f})"
                    )

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
