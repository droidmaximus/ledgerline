import asyncio
import logging
import json
import tempfile
from pathlib import Path

import aiokafka
import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.pageindex_client import PageIndexClient, infer_page_count_from_tree, count_pdf_pages
from app.storage import S3Storage

logger = logging.getLogger(__name__)

class DocumentConsumer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.running = False
        self.consumer = None
        self.producer = None
        self.s3 = S3Storage(settings)
        self.pageindex = PageIndexClient(settings)
        # Limit concurrent processing to avoid overwhelming APIs
        self.processing_semaphore = asyncio.Semaphore(3)
        self.active_tasks = set()
    
    async def start(self):
        """Start consuming documents from Kafka"""
        self.running = True
        
        # Initialize consumer
        self.consumer = aiokafka.AIOKafkaConsumer(
            self.settings.kafka_topic_ingested,
            bootstrap_servers=self.settings.kafka_brokers.split(','),
            group_id=self.settings.kafka_consumer_group,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        # Initialize producer
        self.producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.settings.kafka_brokers.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await self.consumer.start()
        await self.producer.start()
        
        logger.info("Consumer started with concurrent processing (max 3 parallel)")
        
        try:
            async for msg in self.consumer:
                if not self.running:
                    break
                
                # Process messages concurrently without blocking consumer
                task = asyncio.create_task(self._process_message_with_semaphore(msg))
                self.active_tasks.add(task)
                task.add_done_callback(self.active_tasks.discard)
                
            # Wait for remaining tasks to complete
            if self.active_tasks:
                logger.info(f"Waiting for {len(self.active_tasks)} remaining tasks...")
                await asyncio.gather(*self.active_tasks, return_exceptions=True)
        finally:
            await self.consumer.stop()
            await self.producer.stop()
    
    async def _process_message_with_semaphore(self, msg):
        """Process message with concurrency control"""
        async with self.processing_semaphore:
            await self._process_message(msg)
    
    async def _process_message(self, msg):
        """Process a single ingested document message"""
        try:
            message_data = msg.value
            doc_id = message_data.get("doc_id")
            s3_uri = message_data.get("s3_uri")
            filename = message_data.get("filename", "unknown")
            
            logger.info(f"Processing document: {doc_id} ({filename})")
            
            # Download PDF from S3
            pdf_data = await self.s3.download_document(s3_uri)
            
            # Save to temp file for PageIndex
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_data)
                tmp_path = tmp.name
            
            try:
                # Generate tree with PageIndex
                logger.info(f"Generating tree for {doc_id}")
                tree = await self.pageindex.generate_tree(tmp_path)

                page_count = infer_page_count_from_tree(tree) if isinstance(tree, dict) else 0
                if page_count <= 0:
                    page_count = count_pdf_pages(tmp_path)
                if page_count > 0 and isinstance(tree, dict):
                    tree["page_count"] = page_count
                
                # Upload tree to S3
                tree_s3_uri = await self.s3.upload_tree(doc_id, tree)
                
                # Publish parsed event
                parsed_msg = {
                    "doc_id": doc_id,
                    "tree_s3_uri": tree_s3_uri,
                    "filename": filename,
                    "status": "completed",
                    "page_count": page_count,
                    "processing_time_ms": 0
                }
                
                await self.producer.send_and_wait(
                    self.settings.kafka_topic_parsed,
                    value=parsed_msg,
                    key=doc_id.encode('utf-8')
                )
                
                logger.info(f"Document {doc_id} processed successfully")
                
            finally:
                # Clean up temp file
                Path(tmp_path).unlink()
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # TODO: Implement dead letter queue
    
    async def stop(self):
        """Stop the consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()
