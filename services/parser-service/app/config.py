from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    kafka_brokers: str = os.getenv("KAFKA_BROKERS", "localhost:9092")
    kafka_topic_ingested: str = "documents.ingested"
    kafka_topic_parsed: str = "documents.parsed"
    kafka_consumer_group: str = "parser-service"
    s3_bucket_documents: str = os.getenv("S3_BUCKET_DOCUMENTS", "pageindex-documents-dev")
    s3_bucket_trees: str = os.getenv("S3_BUCKET_TREES", "pageindex-trees-dev")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "")
    
    claude_api_key: str = os.getenv("CLAUDE_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    chatgpt_api_key: str = os.getenv("CHATGPT_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    
    pageindex_model: str = os.getenv("PAGEINDEX_MODEL", "gpt-4o-mini")
    parser_service_port: int = int(os.getenv("PARSER_SERVICE_PORT", 8081))
    
    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"
