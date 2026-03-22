import logging
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, func, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import Settings

logger = logging.getLogger(__name__)

Base = declarative_base()

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(String, primary_key=True)
    query_id = Column(String)
    total_score = Column(Float)
    factual_accuracy = Column(Integer)
    completeness = Column(Integer)
    citation_quality = Column(Integer)
    relevance = Column(Integer)
    reasoning = Column(String)
    hallucinations_detected = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)

class EvaluationStorage:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = None
        self.SessionLocal = None
    
    async def init(self):
        """Initialize database"""
        try:
            self.engine = create_async_engine(self.settings.database_url)
            self.SessionLocal = sessionmaker(
                self.engine, 
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database init error: {e}")
    
    async def store_evaluation(self, query_id: str, evaluation: dict):
        """Store evaluation in database"""
        try:
            import uuid
            async with self.SessionLocal() as session:
                eval_record = Evaluation(
                    id=str(uuid.uuid4()),
                    query_id=query_id,
                    total_score=evaluation.get("total_score", 0),
                    factual_accuracy=evaluation.get("factual_accuracy", 0),
                    completeness=evaluation.get("completeness", 0),
                    citation_quality=evaluation.get("citation_quality", 0),
                    relevance=evaluation.get("relevance", 0),
                    reasoning=evaluation.get("reasoning", ""),
                    hallucinations_detected=evaluation.get("hallucinations_detected", False)
                )
                session.add(eval_record)
                await session.commit()
                
            logger.info(f"Evaluation stored for {query_id}")
        except Exception as e:
            logger.error(f"Storage error: {e}")
    
    async def get_recent_evaluations(self, limit: int = 10):
        """Get recent evaluations"""
        try:
            async with self.SessionLocal() as session:
                stmt = (
                    select(Evaluation)
                    .order_by(Evaluation.timestamp.desc())
                    .limit(limit)
                )
                result = await session.scalars(stmt)
                return list(result.all())
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []
    
    async def get_metrics(self):
        """Calculate evaluation metrics"""
        try:
            async with self.SessionLocal() as session:
                total = await session.scalar(select(func.count()).select_from(Evaluation)) or 0
                avg_score = await session.scalar(select(func.avg(Evaluation.total_score)))
                hallucination_count = await session.scalar(
                    select(func.count())
                    .select_from(Evaluation)
                    .where(Evaluation.hallucinations_detected.is_(True))
                ) or 0
                avg_factual = await session.scalar(select(func.avg(Evaluation.factual_accuracy)))
                avg_completeness = await session.scalar(select(func.avg(Evaluation.completeness)))
                avg_citation = await session.scalar(select(func.avg(Evaluation.citation_quality)))
                avg_relevance = await session.scalar(select(func.avg(Evaluation.relevance)))

                hallucination_rate = (hallucination_count / total * 100) if total > 0 else 0.0

                return {
                    "total_evaluated": int(total),
                    "average_score": float(avg_score) if avg_score is not None else 0.0,
                    "hallucination_rate": float(hallucination_rate),
                    "criteria_scores": {
                        "factual_accuracy": float(avg_factual) if avg_factual is not None else 0.0,
                        "completeness": float(avg_completeness) if avg_completeness is not None else 0.0,
                        "citation_quality": float(avg_citation) if avg_citation is not None else 0.0,
                        "relevance": float(avg_relevance) if avg_relevance is not None else 0.0,
                    },
                }
        except Exception as e:
            logger.error(f"Metrics calculation error: {e}")
            return {
                "total_evaluated": 0,
                "average_score": 0.0,
                "hallucination_rate": 0.0,
                "criteria_scores": {},
            }
