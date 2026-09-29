from pathlib import Path

from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter

_converter = None
_chunker = None

def _services():
    global _converter, _chunker
    if _converter is None:
        _converter = DocumentConverter()
    if _chunker is None:
        _chunker = HybridChunker()
    return _converter, _chunker

def process_pdf(file_path: str, original_name: str):
    """Parse one PDF and return contextualized chunks for RAG."""
    converter, chunker = _services()
    result = converter.convert(file_path)
    chunks = chunker.chunk(dl_doc=result.document)

    processed = []
    for index, chunk in enumerate(chunks):
        text = chunker.contextualize(chunk).strip()
        if text:
            processed.append(
                {
                    "id": index,
                    "text": text,
                    "source": Path(original_name).name,
                }
            )

    if not processed:
        raise ValueError("Docling did not extract usable text from the PDF.")

    return processed
