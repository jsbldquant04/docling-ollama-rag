# Deploy to Streamlit Community Cloud

This project is designed so you can deploy it with a public URL.

## 1. Test it locally first

Run:

```powershell
python -m streamlit run app.py
```

Make sure you can upload a PDF and see extracted content.

---

## 2. Create a GitHub repository

Create a new GitHub repository.

Example:

```text
simple-docling-rag
```

Do NOT upload your `.env` file.

The `.gitignore` already prevents this.

---

## 3. Push this project to GitHub

Inside the project folder:

```powershell
git init
git add .
git commit -m "Initial Docling RAG app"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

---

## 4. Open Streamlit Community Cloud

Sign in using your GitHub account.

Create a new app.

Choose:

```text
Repository:
your-username/simple-docling-rag

Branch:
main

Main file:
app.py
```

---

## 5. Add your OpenAI API key

Do NOT put the API key directly inside the source code.

In your Streamlit app settings, open:

```text
Secrets
```

Add:

```toml
OPENAI_API_KEY = "your_real_openai_api_key"
```

Save it.

The code automatically checks Streamlit Secrets when deployed.

---

## 6. Deploy

Click deploy.

Streamlit will:

```text
Read requirements.txt
        ↓
Install dependencies
        ↓
Run app.py
        ↓
Create a public URL
```

Your URL will look similar to:

```text
https://your-app-name.streamlit.app
```

Other people can then:

```text
Open URL
   ↓
Upload their own PDF
   ↓
Ask questions
   ↓
Receive AI answers
```

---

# Important notes

## Docling is heavier than a normal Streamlit app

Docling, Torch, Sentence Transformers, and FAISS require more dependencies than a basic Streamlit app.

If Streamlit Community Cloud runs into memory or build limitations, a later production version can be deployed using:

- Render
- Railway
- Azure
- AWS
- Google Cloud
- Docker

For learning and portfolio demonstration, Streamlit Cloud is still a good first deployment target.

## API usage costs

The embedding model runs locally.

The OpenAI API is used only when generating the final answer.

Keep your API key private.

Never commit `.env` or API keys to GitHub.
