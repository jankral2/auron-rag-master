from contextlib import asynccontextmanager

import uvicorn
from api import router
from db_utils import DatabaseManager
from embedding_service import EmbeddingService
from fastapi import FastAPI
from llm_client import create_llm_client
from loguru import logger
from settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Auron RAG API starting up")
    logger.info("=" * 50)

    app.state.embedding_service = EmbeddingService()
    logger.info("Embedding service initialized")

    app.state.db_manager = DatabaseManager(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    logger.info("Database manager initialized")

    app.state.llm_client = create_llm_client()

    yield

    app.state.db_manager.close_pool()
    logger.info("Auron RAG API shut down")


app = FastAPI(title="Auron RAG API", version="1.0.0", lifespan=lifespan)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
