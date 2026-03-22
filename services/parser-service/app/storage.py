import logging
import json
import zlib

import boto3
from botocore.exceptions import ClientError
import os

from app.config import Settings

logger = logging.getLogger(__name__)

class S3Storage:
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Prepare S3 client kwargs
        s3_kwargs = {
            'region_name': settings.aws_region
        }
        
        # Add explicit credentials from environment
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        if aws_access_key and aws_secret_key:
            s3_kwargs['aws_access_key_id'] = aws_access_key
            s3_kwargs['aws_secret_access_key'] = aws_secret_key
        
        # Add endpoint URL if specified (for MinIO)
        if settings.s3_endpoint_url:
            s3_kwargs['endpoint_url'] = settings.s3_endpoint_url
        
        logger.info(f"Initializing S3 client with endpoint: {settings.s3_endpoint_url}")
        self.s3_client = boto3.client('s3', **s3_kwargs)
    
    async def download_document(self, s3_uri: str) -> bytes:
        """
        Download a document from S3.
        
        Args:
            s3_uri: S3 URI (s3://bucket/key)
            
        Returns:
            Document bytes
        """
        try:
            # Parse S3 URI
            parts = s3_uri.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
            
            logger.info(f"Downloading {s3_uri}")
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            data = response['Body'].read()
            
            logger.info(f"Downloaded {len(data)} bytes")
            return data
            
        except ClientError as e:
            logger.error(f"S3 error: {e}")
            raise
    
    async def upload_tree(self, doc_id: str, tree: dict) -> str:
        """
        Upload a tree JSON to S3.
        
        Args:
            doc_id: Document ID
            tree: Tree dictionary
            
        Returns:
            S3 URI of the uploaded tree
        """
        try:
            key = f"{doc_id}/tree.json"
            
            # Serialize and compress
            tree_json = json.dumps(tree)
            tree_bytes = tree_json.encode('utf-8')
            compressed = zlib.compress(tree_bytes)
            
            logger.info(f"Uploading tree for {doc_id} ({len(compressed)} bytes compressed)")
            
            self.s3_client.put_object(
                Bucket=self.settings.s3_bucket_trees,
                Key=key,
                Body=compressed,
                ContentType='application/json'
            )
            
            s3_uri = f"s3://{self.settings.s3_bucket_trees}/{key}"
            logger.info(f"Uploaded tree to {s3_uri}")
            return s3_uri
            
        except ClientError as e:
            logger.error(f"S3 error: {e}")
            raise
