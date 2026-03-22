import logging
import os
import json
from datetime import datetime, timezone

import aiokafka
import boto3

from app.config import Settings
from app.cache import TreeCache

logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IngestedPendingConsumer:
    """Listens only to documents.ingested with latest offsets — dashboard 'processing' state."""

    def __init__(self, settings: Settings, cache: TreeCache):
        self.settings = settings
        self.cache = cache
        self.running = False
        self.consumer = None

    async def start(self):
        self.running = True
        self.consumer = aiokafka.AIOKafkaConsumer(
            self.settings.kafka_topic_ingested,
            bootstrap_servers=self.settings.kafka_brokers.split(','),
            group_id=f"{self.settings.kafka_consumer_group}-ingested",
            auto_offset_reset='latest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        )
        await self.consumer.start()
        logger.info("Ingested pending consumer started (topic=%s)", self.settings.kafka_topic_ingested)

        try:
            async for msg in self.consumer:
                if not self.running:
                    break
                await self._handle_ingested(msg)
        finally:
            await self.consumer.stop()

    async def _handle_ingested(self, msg):
        try:
            data = msg.value
            doc_id = data.get("doc_id")
            filename = data.get("filename", "unknown")
            ts = data.get("timestamp")
            if isinstance(ts, str) and ts:
                uploaded_at = ts
            else:
                uploaded_at = _iso_now()
            if not doc_id:
                return
            if await self.cache.exists(doc_id):
                return
            await self.cache.set_pending(doc_id, filename, uploaded_at)
        except Exception as e:
            logger.error(f"handle_ingested error: {e}")

    async def stop(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()


class TreeCacheConsumer:
    def __init__(self, settings: Settings, cache: TreeCache):
        self.settings = settings
        self.cache = cache
        self.running = False
        self.consumer = None
    
    async def start(self):
        """Consume parsed documents and warm cache."""
        self.running = True
        
        self.consumer = aiokafka.AIOKafkaConsumer(
            self.settings.kafka_topic_parsed,
            bootstrap_servers=self.settings.kafka_brokers.split(','),
            group_id=self.settings.kafka_consumer_group,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        await self.consumer.start()
        logger.info("Cache consumer started (topic=%s)", self.settings.kafka_topic_parsed)
        
        try:
            async for msg in self.consumer:
                if not self.running:
                    break
                await self._process_parsed_message(msg)
        finally:
            await self.consumer.stop()
    
    async def _process_parsed_message(self, msg):
        """Process a parsed document message and warm cache"""
        try:
            message_data = msg.value
            doc_id = message_data.get("doc_id")
            tree_s3_uri = message_data.get("tree_s3_uri")
            filename = message_data.get("filename", "unknown")
            
            logger.info(f"Warming cache for {doc_id} ({filename})")
            
            s3_kwargs = {
                'region_name': self.settings.aws_region
            }
            
            aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            if aws_access_key and aws_secret_key:
                s3_kwargs['aws_access_key_id'] = aws_access_key
                s3_kwargs['aws_secret_access_key'] = aws_secret_key
            
            if self.settings.s3_endpoint_url:
                s3_kwargs['endpoint_url'] = self.settings.s3_endpoint_url
            
            s3_client = boto3.client('s3', **s3_kwargs)
            
            parts = tree_s3_uri.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
            
            response = s3_client.get_object(Bucket=bucket, Key=key)
            tree_data = response['Body'].read()
            
            import zlib
            decompressed = zlib.decompress(tree_data)
            tree = json.loads(decompressed.decode('utf-8'))
            
            pending = await self.cache.get_pending(doc_id)
            uploaded_at = None
            if pending:
                uploaded_at = pending.get("uploaded_at")
            if not uploaded_at:
                uploaded_at = _iso_now()
            page_count = int(
                message_data.get("page_count")
                or tree.get("page_count")
                or 0
            )
            
            await self.cache.set(
                doc_id,
                tree,
                filename=filename,
                page_count=page_count,
                uploaded_at=uploaded_at,
            )
            await self.cache.clear_pending(doc_id)
            
            logger.info(f"Cache warmed for {doc_id}")
            
        except Exception as e:
            logger.error(f"Error warming cache: {e}")
    
    async def stop(self):
        """Stop the consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
