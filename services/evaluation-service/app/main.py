import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Populate os.environ before Settings() so DATABASE_URL etc. match repo-root .env
# when running from services/evaluation-service (cwd has no .env).
_eval_root = Path(__file__).resolve().parent.parent
_repo_root = Path(__file__).resolve().parents[3]
for _env_path in (_eval_root / ".env", _repo_root / ".env"):
    if _env_path.is_file():
        load_dotenv(_env_path, override=True)

from app.config import Settings
from app.consumer import QueryEvaluationConsumer
from app.storage import EvaluationStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()
storage = EvaluationStorage(settings)
consumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Evaluation Service")
    
    # Initialize database
    await storage.init()
    
    global consumer
    consumer = QueryEvaluationConsumer(settings, storage)
    
    # Start consumer in background
    consumer_task = asyncio.create_task(consumer.start())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Evaluation Service")
    if consumer:
        await consumer.stop()
    try:
        await asyncio.wait_for(consumer_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.error("Consumer did not stop gracefully")

app = FastAPI(
    title="Evaluation Service",
    description="LLM-as-a-Judge evaluation of query responses",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "evaluation"}
    )

@app.get("/evaluations")
async def list_evaluations(limit: int = 10):
    """List recent evaluations"""
    evaluations = await storage.get_recent_evaluations(limit)
    result = []
    for eval_record in evaluations:
        result.append({
            "id": eval_record.id,
            "query_id": eval_record.query_id,
            "score": eval_record.total_score,
            "reasoning": eval_record.reasoning,
            "timestamp": eval_record.timestamp.isoformat() if eval_record.timestamp else None,
            "factual_accuracy": eval_record.factual_accuracy,
            "completeness": eval_record.completeness,
            "citation_quality": eval_record.citation_quality,
            "relevance": eval_record.relevance,
            "hallucinations_detected": eval_record.hallucinations_detected,
        })
    return JSONResponse(
        status_code=200,
        content={"evaluations": result}
    )

@app.get("/metrics")
async def metrics():
    """Get evaluation metrics"""
    metrics_data = await storage.get_metrics()
    return JSONResponse(
        status_code=200,
        content=metrics_data
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("EVALUATION_SERVICE_PORT", 8084)))
