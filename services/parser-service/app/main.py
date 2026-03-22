import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import logging
from pathlib import Path

from app.config import Settings
from app.consumer import DocumentConsumer

# Load .env from service dir or repo root (matches Go services / gateway)
_svc_root = Path(__file__).resolve().parent.parent
_repo_root = _svc_root.parent.parent
for _env_path in (_svc_root / ".env", _repo_root / ".env"):
    if _env_path.is_file():
        load_dotenv(_env_path, override=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()
consumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Parser Service")
    global consumer
    consumer = DocumentConsumer(settings)
    
    # Start consumer in background
    consumer_task = asyncio.create_task(consumer.start())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Parser Service")
    if consumer:
        await consumer.stop()
    # Cancel the consumer task and wait for it to finish
    if not consumer_task.done():
        consumer_task.cancel()
    try:
        await asyncio.wait_for(consumer_task, timeout=5.0)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        logger.info("Consumer task cancelled")

app = FastAPI(
    title="Parser Service",
    description="Document parsing with PageIndex",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "parser"}
    )

@app.get("/metrics")
async def metrics():
    # TODO: Return processing metrics
    return JSONResponse(
        status_code=200,
        content={
            "documents_processed": 0,
            "avg_processing_time_ms": 0,
            "errors": 0
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PARSER_SERVICE_PORT", 8081)))
