# FastAPI backend pro Auron RAG
FROM python:3.12-slim

WORKDIR /app

# Instalace systemovych zavislosti
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Kopirovani requirements
COPY requirements.txt .

# Instalace Python dependencies s uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --link-mode=copy -r requirements.txt

# Kopirovani aplikace
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Environment promenne
ENV PYTHONUNBUFFERED=1

# Spusteni FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
