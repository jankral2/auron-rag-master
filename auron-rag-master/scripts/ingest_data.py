"""
Data ingestion script - loads .txt documents into the vector database.
"""

import os
import sys
from pathlib import Path
from typing import List

import psycopg2
from sentence_transformers import SentenceTransformer


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 50) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def connect_to_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def ingest_documents(data_dir: str):
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Connecting to database...")
    conn = connect_to_db()
    cursor = conn.cursor()

    print("Clearing existing documents...")
    cursor.execute("DELETE FROM documents")
    conn.commit()

    data_path = Path(data_dir)
    txt_files = sorted(data_path.glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {data_dir}")
        sys.exit(1)

    print(f"Found {len(txt_files)} files\n")

    total_chunks = 0

    for txt_file in txt_files:
        try:
            content = txt_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  [{txt_file.name}] read error: {e}")
            continue

        if not content.strip():
            print(f"  [{txt_file.name}] empty, skipping")
            continue

        slug = None
        for line in content.splitlines():
            if line.startswith("Slug:"):
                slug = line.split(":", 1)[1].strip()
                break
        url = f"/#/article/{slug}" if slug else None

        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            try:
                embedding = model.encode(chunk).tolist()
                cursor.execute(
                    """
                    INSERT INTO documents (text, filename, source_type, chunk_index, url, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (chunk, txt_file.name, "article", i, url, embedding),
                )
            except Exception as e:
                print(f"  [{txt_file.name}] chunk {i} error: {e}")
                continue

        conn.commit()
        total_chunks += len(chunks)
        print(f"  [{txt_file.name}] {len(chunks)} chunks")

    cursor.close()
    conn.close()

    print(f"\nDone. {len(txt_files)} files, {total_chunks} chunks total.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_data.py <data_dir>")
        sys.exit(1)

    data_dir = sys.argv[1]

    if not Path(data_dir).exists():
        print(f"Error: directory '{data_dir}' does not exist")
        sys.exit(1)

    ingest_documents(data_dir)
