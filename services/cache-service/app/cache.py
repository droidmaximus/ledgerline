import json
import zlib
import logging

import redis.asyncio as redis

from app.config import Settings

logger = logging.getLogger(__name__)

class TreeCache:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.redis_client = None
    
    async def _get_client(self):
        """Lazy initialize Redis client"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                f"redis://:{self.settings.redis_password}@{self.settings.redis_host}:{self.settings.redis_port}",
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client
    
    async def get(self, doc_id: str):
        """Get tree from cache"""
        try:
            client = await self._get_client()
            key = f"tree:{doc_id}"
            
            data = await client.get(key)
            if not data:
                return None
            
            # Decompress
            decompressed = zlib.decompress(bytes.fromhex(data))
            return json.loads(decompressed.decode('utf-8'))
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        doc_id: str,
        tree: dict,
        ttl: int = None,
        filename: str = None,
        page_count: int = None,
        uploaded_at: str = None,
    ):
        """Set tree in cache"""
        try:
            client = await self._get_client()
            key = f"tree:{doc_id}"
            metadata_key = f"metadata:{doc_id}"
            ttl = ttl or self.settings.redis_ttl
            
            # Compress and store tree as hex
            tree_json = json.dumps(tree)
            compressed = zlib.compress(tree_json.encode('utf-8'))
            hex_data = compressed.hex()
            
            await client.set(key, hex_data, ex=ttl)
            
            metadata = {"filename": filename or doc_id, "doc_id": doc_id}
            if page_count is not None:
                metadata["pages"] = int(page_count)
            if uploaded_at:
                metadata["uploaded_at"] = uploaded_at
            await client.set(metadata_key, json.dumps(metadata), ex=ttl)
            
            logger.info(f"Cached tree for {doc_id}")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def set_pending(self, doc_id: str, filename: str, uploaded_at: str):
        """Mark document as in pipeline (ingested, not yet parsed)."""
        try:
            client = await self._get_client()
            key = f"pending:{doc_id}"
            payload = json.dumps({
                "doc_id": doc_id,
                "filename": filename,
                "uploaded_at": uploaded_at,
            })
            await client.set(key, payload, ex=86400)
            logger.info(f"Pending registered for {doc_id}")
        except Exception as e:
            logger.error(f"set_pending error: {e}")

    async def get_pending(self, doc_id: str):
        try:
            client = await self._get_client()
            raw = await client.get(f"pending:{doc_id}")
            if not raw:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.error(f"get_pending error: {e}")
            return None

    async def clear_pending(self, doc_id: str):
        try:
            client = await self._get_client()
            await client.delete(f"pending:{doc_id}")
        except Exception as e:
            logger.error(f"clear_pending error: {e}")

    async def list_pending_keys(self) -> list:
        try:
            client = await self._get_client()
            return await client.keys("pending:*")
        except Exception as e:
            logger.error(f"list_pending_keys error: {e}")
            return []
    
    async def delete(self, doc_id: str):
        """Delete tree from cache"""
        try:
            client = await self._get_client()
            key = f"tree:{doc_id}"
            await client.delete(key)
            logger.info(f"Deleted cache for {doc_id}")
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def exists(self, doc_id: str) -> bool:
        """Check if tree exists in cache"""
        try:
            client = await self._get_client()
            key = f"tree:{doc_id}"
            return await client.exists(key)
            
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    async def get_all_keys(self) -> list:
        """Get all cached tree keys"""
        try:
            client = await self._get_client()
            keys = await client.keys("tree:*")
            return keys
            
        except Exception as e:
            logger.error(f"Cache keys error: {e}")
            return []
    
    async def get_metadata(self, doc_id: str):
        """Get metadata for a document"""
        try:
            client = await self._get_client()
            metadata_key = f"metadata:{doc_id}"
            
            data = await client.get(metadata_key)
            if not data:
                return None
            
            return json.loads(data)
            
        except Exception as e:
            logger.error(f"Cache metadata get error: {e}")
            return None
