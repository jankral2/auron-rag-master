from typing import List

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel

router = APIRouter()


def _extract_title(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("Název:"):
            return line.split(":", 1)[1].strip()
    return None


class RagRequest(BaseModel):
    query: str
    top_k: int = 5


class Source(BaseModel):
    title: str | None = None
    url: str | None = None
    similarity: float


class RagResponse(BaseModel):
    answer: str
    sources: List[Source]


class DirectChatRequest(BaseModel):
    message: str
    system_prompt: str | None = None


class DirectChatResponse(BaseModel):
    answer: str


@router.post("/api/rag", response_model=RagResponse)
async def rag_query(request: RagRequest, req: Request):
    embedding_service = req.app.state.embedding_service
    db_manager = req.app.state.db_manager
    llm_client = req.app.state.llm_client
    try:
        logger.info(
            f"POST /api/rag | query='{request.query[:60]}' top_k={request.top_k}"
        )

        query_embedding = embedding_service.encode(request.query)
        documents = db_manager.search_similar(query_embedding, top_k=request.top_k)

        logger.info(f"  retrieved {len(documents)} chunks:")
        for doc in documents:
            logger.info(
                f"    chunk={doc['chunk_index']} sim={doc['similarity']:.3f} url={doc.get('url')} file={doc['filename']}"
            )

        llm_response = llm_client.rag_chat(query=request.query, documents=documents)

        # Build sources only from documents the LLM actually used
        used_set = set(llm_response.used_documents)
        used_docs = [doc for doc in documents if doc["filename"] in used_set]

        # Deduplicate by URL (multiple chunks from same article), keep highest similarity
        seen: dict[str, Source] = {}
        for doc in used_docs:
            key = doc.get("url") or doc["filename"]
            source = Source(
                title=_extract_title(doc["text"]) or doc["filename"],
                url=doc.get("url"),
                similarity=doc["similarity"],
            )
            if key not in seen or source.similarity > seen[key].similarity:
                seen[key] = source
        sources = list(seen.values())

        logger.info(f"  used_documents from LLM: {llm_response.used_documents}")
        logger.info(f"  sources after dedup ({len(sources)}):")
        for s in sources:
            logger.info(f"    '{s.title}' -> {s.url} (sim={s.similarity:.3f})")
        logger.info(f"  answer: '{llm_response.text[:120]}'")

        return RagResponse(answer=llm_response.text, sources=sources)

    except Exception as e:
        logger.error(f"POST /api/rag error: {e}")
        raise HTTPException(status_code=500, detail="Error processing RAG query")


@router.post("/api/llm", response_model=DirectChatResponse)
async def direct_llm(request: DirectChatRequest, req: Request):
    llm_client = req.app.state.llm_client
    try:
        logger.info(f"POST /api/llm | message='{request.message[:60]}'")
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.message})
        answer = llm_client.direct_chat(messages)
        logger.info(f"  answer: '{answer[:120]}'")
        return DirectChatResponse(answer=answer)
    except Exception as e:
        logger.error(f"POST /api/llm error: {e}")
        raise HTTPException(status_code=500, detail="Error calling LLM")


@router.get("/api/health")
async def health_check():
    logger.debug("GET /api/health")
    return {"status": "healthy", "service": "Auron RAG API"}


@router.get("/api/stats")
async def get_stats(req: Request):
    db_manager = req.app.state.db_manager
    try:
        count = db_manager.count_documents()
        logger.info(f"GET /api/stats | document_count={count}")
        return {"document_count": count}
    except Exception as e:
        logger.error(f"GET /api/stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
