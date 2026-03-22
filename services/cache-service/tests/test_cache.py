import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings

client = TestClient(app)

class TestHealthEndpoint:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "cache"

class TestCacheStats:
    def test_cache_stats(self):
        """Test cache statistics endpoint"""
        response = client.get("/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "hits" in data
        assert "misses" in data
        assert "cached_items" in data
        assert "hit_rate" in data

class TestConfig:
    def test_settings_load(self):
        """Test configuration loading"""
        settings = Settings()
        assert settings.redis_host
        assert settings.redis_port
        assert settings.kafka_consumer_group == "cache-service"
        assert settings.redis_ttl == 3600

class TestCacheOperations:
    @pytest.mark.asyncio
    async def test_cache_client_initialization(self):
        """Test cache client initialization"""
        from app.cache import TreeCache
        
        settings = Settings()
        cache = TreeCache(settings)
        assert cache is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
