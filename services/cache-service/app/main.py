import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import logging
from pathlib import Path
from prometheus_client import Counter, Gauge, Histogram, generate_latest

from app.config import Settings
from app.consumer import TreeCacheConsumer, IngestedPendingConsumer
from app.cache import TreeCache

_svc_root = Path(__file__).resolve().parent.parent
_repo_root = _svc_root.parent.parent
for _env_path in (_svc_root / ".env", _repo_root / ".env"):
    if _env_path.is_file():
        load_dotenv(_env_path, override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()
cache = TreeCache(settings)
consumer = None
ingested_consumer = None

cache_hits = Counter('cache_hits_total', 'Total cache hits')
cache_misses = Counter('cache_misses_total', 'Total cache misses')
cache_operations = Histogram('cache_operations_duration_seconds', 'Cache operation duration')
cached_trees = Gauge('cached_trees_count', 'Number of cached trees')


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Cache Service")
    global consumer, ingested_consumer
    consumer = TreeCacheConsumer(settings, cache)
    ingested_consumer = IngestedPendingConsumer(settings, cache)
    
    consumer_task = asyncio.create_task(consumer.start())
    ingested_task = asyncio.create_task(ingested_consumer.start())
    
    yield
    logger.info("Shutting down Cache Service")
    if consumer:
        await consumer.stop()
    if ingested_consumer:
        await ingested_consumer.stop()
    try:
        await asyncio.wait_for(asyncio.gather(consumer_task, ingested_task), timeout=5.0)
    except asyncio.TimeoutError:
        logger.error("Consumers did not stop gracefully")

app = FastAPI(
    title="Cache Service",
    description="Redis tree caching service",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "cache"}
    )

@app.get("/cache/tree/{doc_id}")
async def get_tree(doc_id: str):
    """GET tree by doc id (Redis + S3 fallback in cache layer)."""
    with cache_operations.time():
        max_attempts = 4
        retry_delay_seconds = 0.4
        tree = None

        for attempt in range(1, max_attempts + 1):
            tree = await cache.get(doc_id)
            if tree:
                break
            if attempt < max_attempts:
                await asyncio.sleep(retry_delay_seconds)

        if tree:
            cache_hits.inc()
            if max_attempts > 1 and attempt > 1:
                logger.info(f"Cache hit for {doc_id} after retry {attempt}/{max_attempts}")
            else:
                logger.info(f"Cache hit for {doc_id}")
        else:
            cache_misses.inc()
            logger.info(f"Cache miss for {doc_id} after {max_attempts} attempts")
        
        cached_trees.set(len(await cache.get_all_keys()))
        
        if not tree:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        
        return JSONResponse(status_code=200, content=tree)

@app.delete("/cache/tree/{doc_id}")
async def delete_tree(doc_id: str):
    """DELETE cached tree."""
    await cache.delete(doc_id)
    logger.info(f"Invalidated cache for {doc_id}")
    return JSONResponse(status_code=200, content={"status": "deleted"})

@app.get("/cache/stats")
async def cache_stats():
    """Hit/miss counters."""
    return JSONResponse(
        status_code=200,
        content={
            "hits": cache_hits._value.get(),
            "misses": cache_misses._value.get(),
            "cached_items": len(await cache.get_all_keys()),
            "hit_rate": cache_hits._value.get() / (cache_hits._value.get() + cache_misses._value.get()) if (cache_hits._value.get() + cache_misses._value.get()) > 0 else 0
        }
    )

@app.get("/documents")
async def list_documents():
    """Pending ingest + trees in Redis."""
    keys = await cache.get_all_keys()
    pending_keys = await cache.list_pending_keys()
    tree_doc_ids = set()
    documents = []
    for key in keys:
        doc_id = key.replace("tree:", "")
        tree_doc_ids.add(doc_id)
        metadata = await cache.get_metadata(doc_id) or {}
        filename = metadata.get("filename", doc_id)
        pages = int(metadata.get("pages", 0))
        uploaded_at = metadata.get("uploaded_at") or ""
        documents.append({
            "doc_id": doc_id,
            "filename": filename,
            "pages": pages,
            "uploaded_at": uploaded_at,
            "status": "completed",
        })
    for pk in pending_keys:
        doc_id = pk.replace("pending:", "")
        if doc_id in tree_doc_ids:
            continue
        raw = await cache.get_pending(doc_id)
        if not raw:
            continue
        documents.append({
            "doc_id": doc_id,
            "filename": raw.get("filename", doc_id),
            "pages": 0,
            "uploaded_at": raw.get("uploaded_at", ""),
            "status": "processing",
        })
    documents.sort(key=lambda d: d.get("uploaded_at") or "", reverse=True)
    return JSONResponse(
        status_code=200,
        content={"documents": documents}
    )

@app.get("/metrics")
async def metrics():
    """Prometheus scrape."""
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("CACHE_SERVICE_PORT", 8082)))
