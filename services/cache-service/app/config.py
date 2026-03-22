from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_ttl: int = int(os.getenv("REDIS_TTL", 3600))
    
    # Kafka
    kafka_brokers: str = os.getenv("KAFKA_BROKERS", "localhost:9092")
    kafka_topic_parsed: str = "documents.parsed"
    kafka_topic_ingested: str = "documents.ingested"
    kafka_consumer_group: str = "cache-service"
    
    # S3
    s3_bucket_trees: str = os.getenv("S3_BUCKET_TREES", "pageindex-trees-dev")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "")
    
    # AWS Credentials (for MinIO)
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
    
    # Service
    cache_service_port: int = int(os.getenv("CACHE_SERVICE_PORT", 8082))
    
    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"
