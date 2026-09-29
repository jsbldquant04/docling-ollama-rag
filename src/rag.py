from openai import OpenAI

def answer_question(question, vector_store, api_key, model="gpt-5-mini"):
    results = vector_store.search(question, limit=5)

    if not results:
        return {
            "answer": "I could not find indexed document content. Upload a PDF first.",
            "sources": [],
        }

    context = "\n\n".join(
        f"[Source {i + 1}: {item['source']}, chunk {item['chunk_id']}]\n{item['text']}"
        for i, item in enumerate(results)
    )

    prompt = f"""You are a careful research-paper and financial-report assistant.

Answer ONLY from the supplied document context.
If the answer is not supported by the context, say that the uploaded document
does not provide enough information. Do not invent facts, numbers, citations,
or page numbers.

When useful, refer to the source chunk numbers shown in the context.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}
"""

    client = OpenAI(api_key=api_key)
    response = client.responses.create(model=model, input=prompt)

    return {
        "answer": response.output_text,
        "sources": [
            {
                "source": item["source"],
                "chunk_id": item["chunk_id"],
                "score": item["score"],
            }
            for item in results
        ],
    }
