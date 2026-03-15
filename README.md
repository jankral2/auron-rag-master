# Auron RAG — Demo Intranet

A demo company intranet with an AI assistant (Auron GPT) powered by RAG (Retrieval-Augmented Generation). The AI can answer questions about internal articles and return clickable links to the relevant pages.

## Architecture

```
data/*.txt  ──► generate_data_js.py ──► frontend/data.js ──► Browser (articles with URLs)
data/*.txt  ──► ingest_data.py      ──► PostgreSQL + pgvector
                                              │
                                     FastAPI /api/rag
                                              │
                                        SkodaGPT LLM ──► answer with [Title](url) links
```

| Component  | Technology |
|------------|-----------|
| Frontend   | HTML + Tailwind CSS + Vanilla JS |
| Backend    | FastAPI (Python) |
| Database   | PostgreSQL 17 + pgvector |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| LLM        | SkodaGPT (custom REST API) |
| Web server | Nginx |

## Initial Setup

### 1. Prerequisites

- Docker & Docker Compose
- Python 3.10+

### 2. Configure environment

```bash
cp .env.template .env
# Edit .env and fill in:
#   SKODAGPT_ENDPOINT=...
#   SKODAGPT_API_KEY=...
```

### 3. Generate frontend article data

```bash
python3 scripts/generate_data_js.py
# Reads data/*.txt → writes frontend/data.js
```

### 4. Start services

```bash
docker-compose up -d
```

### 5. Ingest articles into vector DB

```bash
docker compose --profile ingest up ingest
```

### 6. Open the app

```
http://localhost:8081
```

---

## Editing Content

Articles live in `data/*.txt` — this is the **single source of truth**.

**Article format:**
```
Rubrika: Marketing
Datum: 02. 03. 2026
Slug: 01_marketing
Název: Spuštění interní kampaně k novému modelu

Article body text goes here.
Multiple paragraphs are supported.
```

**After editing or adding articles:**

```bash
# 1. Regenerate frontend data
python3 scripts/generate_data_js.py

# 2. Re-ingest into vector DB (if Docker is running)
docker compose --profile ingest up ingest
```

### Section → Category mapping

| Nav section          | Rubrika in .txt files          |
|----------------------|-------------------------------|
| O společnosti        | Marketing                      |
| Organizace           | Správa majetku                 |
| Pracovní informace   | Výroba, Nákup                  |
| Život a kariéra      | Personální informace           |
| Služby               | IT, IT Provoz                  |
| Odměňování a benefity| Investice                      |
| Strategie            | Vývoj                          |

---

## URL Structure

Each article is accessible at:
```
http://localhost:8081/#/article/{slug}
```

Example: `http://localhost:8081/#/article/01_marketing`

These URLs are stored in the vector DB during ingestion. When Auron GPT finds a relevant article, it returns a clickable markdown link `[Title](url)` that opens the article directly.
