import os
import tempfile

import faiss
import requests
import streamlit as st
from docling.document_converter import DocumentConverter
from sentence_transformers import SentenceTransformer


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"


st.set_page_config(
    page_title="Docling PDF AI Assistant",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Docling PDF AI Assistant")
st.caption(
    "Upload a PDF, search it semantically, and ask questions using a local Ollama model."
)


@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def extract_pdf(uploaded_file):
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as tmp:
            tmp.write(uploaded_file.getbuffer())
            temp_path = tmp.name

        converter = DocumentConverter()
        result = converter.convert(temp_path)

        return result.document.export_to_markdown()

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def chunk_text(
    text,
    chunk_size=1200,
    overlap=200,
):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def build_index(chunks):
    model = load_embedding_model()

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype("float32")

    index = faiss.IndexFlatIP(
        embeddings.shape[1]
    )

    index.add(embeddings)

    return index


def search(
    question,
    chunks,
    index,
    top_k=4,
):
    model = load_embedding_model()

    query_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype("float32")

    scores, ids = index.search(
        query_embedding,
        min(top_k, len(chunks)),
    )

    results = []

    for score, idx in zip(
        scores[0],
        ids[0],
    ):
        if idx != -1:
            results.append(
                {
                    "score": float(score),
                    "text": chunks[idx],
                }
            )

    return results


def ollama_is_running():
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=3,
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


def answer_with_llm(
    question,
    results,
):
    context = "\n\n".join(
        f"[Source {i}]\n{item['text']}"
        for i, item in enumerate(
            results,
            start=1,
        )
    )

    prompt = f"""
You are a careful research paper assistant.

Answer the user's question using ONLY the provided document context.

Rules:
- Do not invent facts.
- Base your answer only on the retrieved document context.
- Explain technical ideas clearly.
- If the context does not contain enough information, say:
  "I could not find enough information in the document."
- When useful, mention the source number supporting the answer.

Question:
{question}

Document context:
{context}

Answer:
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2,
                },
            },
            timeout=180,
        )

        response.raise_for_status()

        data = response.json()

        return data["message"]["content"]

    except requests.ConnectionError:
        return (
            "Could not connect to Ollama. "
            "Make sure Ollama is installed and running."
        )

    except requests.Timeout:
        return (
            "Ollama took too long to respond. "
            "Try again or use a smaller model."
        )

    except requests.RequestException as error:
        return f"Ollama request failed: {error}"

    except KeyError:
        return (
            "Ollama returned an unexpected response format."
        )


if not ollama_is_running():
    st.warning(
        "Ollama is not running. "
        "Start Ollama before asking questions."
    )
else:
    st.success(
        f"Ollama connected · Model: {OLLAMA_MODEL}"
    )


uploaded_file = st.file_uploader(
    "Upload a research paper or financial report",
    type=["pdf"],
)


if uploaded_file:
    file_signature = (
        f"{uploaded_file.name}-"
        f"{uploaded_file.size}"
    )

    if (
        st.session_state.get("file_signature")
        != file_signature
    ):
        with st.spinner(
            "Reading the PDF with Docling..."
        ):
            markdown = extract_pdf(
                uploaded_file
            )

        with st.spinner(
            "Creating document chunks and embeddings..."
        ):
            chunks = chunk_text(
                markdown
            )

            index = build_index(
                chunks
            )

        st.session_state.file_signature = (
            file_signature
        )

        st.session_state.markdown = (
            markdown
        )

        st.session_state.chunks = (
            chunks
        )

        st.session_state.index = (
            index
        )

    st.success(
        f"Ready: {uploaded_file.name}"
    )

    tab1, tab2 = st.tabs(
        [
            "💬 Ask",
            "📄 Extracted text",
        ]
    )

    with tab1:
        question = st.text_input(
            "Ask a question about the PDF",
            placeholder=(
                "Example: What are the main findings?"
            ),
        )

        if (
            st.button(
                "Ask question",
                type="primary",
            )
            and question.strip()
        ):
            if not ollama_is_running():
                st.error(
                    "Ollama is not running. "
                    "Start Ollama first."
                )

            else:
                results = search(
                    question,
                    st.session_state.chunks,
                    st.session_state.index,
                )

                with st.spinner(
                    "Generating answer with Ollama..."
                ):
                    answer = answer_with_llm(
                        question,
                        results,
                    )

                st.subheader("Answer")
                st.write(answer)

                st.subheader(
                    "Retrieved sources"
                )

                for i, result in enumerate(
                    results,
                    start=1,
                ):
                    with st.expander(
                        f"Source {i} · "
                        f"similarity "
                        f"{result['score']:.3f}"
                    ):
                        st.write(
                            result["text"]
                        )

    with tab2:
        st.markdown(
            st.session_state.markdown
        )

        st.download_button(
            "Download extracted Markdown",
            data=st.session_state.markdown,
            file_name=(
                "extracted_document.md"
            ),
            mime="text/markdown",
        )

else:
    st.info(
        "Upload a PDF to start."
    )