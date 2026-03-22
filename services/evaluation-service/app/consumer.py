import json
import logging
import random

import aiokafka

from app.config import Settings
from app.judge import LLMJudge
from app.storage import EvaluationStorage

logger = logging.getLogger(__name__)

class QueryEvaluationConsumer:
    def __init__(self, settings: Settings, storage: EvaluationStorage):
        self.settings = settings
        self.storage = storage
        self.running = False
        self.consumer = None
        self.judge = LLMJudge(settings)
    
    async def start(self):
        """Start consuming queries for evaluation"""
        self.running = True
        
        self.consumer = aiokafka.AIOKafkaConsumer(
            self.settings.kafka_topic_queries,
            bootstrap_servers=self.settings.kafka_brokers.split(','),
            group_id=self.settings.kafka_consumer_group,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        await self.consumer.start()
        logger.info("Evaluation consumer started")
        
        try:
            async for msg in self.consumer:
                if not self.running:
                    break
                
                await self._process_message(msg)
        finally:
            await self.consumer.stop()
    
    async def _process_message(self, msg):
        """Process a query and evaluate it"""
        try:
            message_data = msg.value
            query_id = message_data.get("query_id")
            
            # Sample based on configured rate
            if random.random() > self.settings.evaluation_sampling_rate:
                logger.debug(f"Skipping evaluation for {query_id} (sampling)")
                return
            
            logger.info(f"Evaluating query {query_id}")
            
            # Judge the answer (include tree_path so citation quality reflects gateway references)
            question = message_data.get("question")
            answer = message_data.get("answer")
            tree_path = message_data.get("tree_path")

            evaluation = await self.judge.judge_answer(question, answer, tree_path=tree_path)
            
            # Store evaluation
            await self.storage.store_evaluation(query_id, evaluation)
            
            logger.info(f"Evaluation stored for {query_id}: score={evaluation['total_score']}")
            
        except Exception as e:
            logger.error(f"Error evaluating query: {e}")
    
    async def stop(self):
        """Stop the consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
