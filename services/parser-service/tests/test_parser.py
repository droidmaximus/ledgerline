import pytest
import asyncio
from unittest.mock import patch, AsyncMock
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
        assert response.json()["service"] == "parser"

class TestMetrics:
    def test_metrics_endpoint(self):
        """Test metrics endpoint returns valid structure"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "documents_processed" in data
        assert "avg_processing_time_ms" in data
        assert "errors" in data

class TestPageIndexClient:
    @pytest.mark.asyncio
    async def test_pageindex_client_initialization(self):
        """Test PageIndex client can be initialized"""
        from app.pageindex_client import PageIndexClient
        
        settings = Settings()
        client = PageIndexClient(settings)
        assert client is not None

class TestConfig:
    def test_settings_load(self):
        """Test configuration loading"""
        settings = Settings()
        assert settings.kafka_brokers
        assert settings.s3_bucket_documents
        assert settings.s3_bucket_trees
        assert settings.kafka_consumer_group == "parser-service"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
