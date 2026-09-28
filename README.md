# Simple Docling RAG Deployment

A small, deployment-ready AI document assistant built with:

- Streamlit
- Docling
- Sentence Transformers
- FAISS
- OpenAI API

## What it does

```text
Upload PDF
   ↓
Docling extracts structured Markdown
   ↓
Text is split into chunks
   ↓
Local embeddings are created
   ↓
FAISS searches relevant chunks
   ↓
OpenAI generates an answer
```

You can upload:

- research papers
- annual reports
- financial reports
- theses
- technical PDFs

Example questions:

```text
What is the main methodology?

What are the key findings?

What risks are mentioned?

Why did revenue change?

Summarize this report.
```

## Recommended Python

Use Python 3.12.

## Local setup

Open the folder in VS Code.

Create a virtual environment:

```powershell
py -3.12 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy:

```text
.env.example
```

to:

```text
.env
```

Then add your API key:

```text
OPENAI_API_KEY=your_real_key_here
```

Run:

```powershell
python -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Deploy

See `DEPLOY.md`.
