from contextlib import contextmanager
from typing import Dict, List

from loguru import logger
from psycopg2 import pool


class DatabaseManager:
    """Manager for database operations using a connection pool."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        min_conn: int = 1,
        max_conn: int = 10,
    ):
        self._pool = pool.ThreadedConnectionPool(
            min_conn,
            max_conn,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        logger.info(f"Database pool initialized: {host}:{port}/{database}")

    def close_pool(self) -> None:
        """Close all connections in the pool."""
        self._pool.closeall()
        logger.info("Database pool closed")

    @contextmanager
    def _get_cursor(self):
        """Context manager that checks out a connection, yields (conn, cursor),
        commits on success, rolls back on error, and returns the connection to the pool."""
        conn = self._pool.getconn()
        cursor = None
        try:
            cursor = conn.cursor()
            yield conn, cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self._pool.putconn(conn)

    def search_similar(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict]:
        """Find similar documents using vector similarity."""
        logger.debug(f"Searching for {top_k} similar documents")
        query = """
            SELECT
                id,
                text,
                filename,
                source_type,
                chunk_index,
                url,
                1 - (embedding <=> %s::vector) as similarity
            FROM documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        with self._get_cursor() as (_, cursor):
            cursor.execute(query, (query_embedding, query_embedding, top_k))
            results = cursor.fetchall()

        logger.debug(f"Database returned {len(results)} results")
        return [
            {
                "id": row[0],
                "text": row[1],
                "filename": row[2],
                "source_type": row[3],
                "chunk_index": row[4],
                "url": row[5],
                "similarity": row[6],
            }
            for row in results
        ]

    def insert_document(self, document_data: Dict, embedding: List[float]) -> int:
        """Insert a document with its embedding. Raises ValueError if required fields are missing."""
        required = ("text", "filename", "source_type", "chunk_index")
        missing = [k for k in required if k not in document_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        logger.debug(f"Inserting document: {document_data['filename']}")
        query = """
            INSERT INTO documents (
                text, filename, source_type, chunk_index, embedding
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        with self._get_cursor() as (_, cursor):
            cursor.execute(
                query,
                (
                    document_data["text"],
                    document_data["filename"],
                    document_data["source_type"],
                    document_data["chunk_index"],
                    embedding,
                ),
            )
            return cursor.fetchone()[0]

    def count_documents(self) -> int:
        """Return the total number of documents."""
        with self._get_cursor() as (_, cursor):
            cursor.execute("SELECT COUNT(*) FROM documents")
            return cursor.fetchone()[0]

    def clear_documents(self) -> None:
        """Delete all documents from the database."""
        logger.info("Clearing all documents from database")
        with self._get_cursor() as (_, cursor):
            cursor.execute("DELETE FROM documents")
        logger.info("All documents cleared")
