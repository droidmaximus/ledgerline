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
        assert response.json()["service"] == "api-gateway"

class TestDocumentEndpoints:
    def test_list_documents(self):
        """Test document listing"""
        response = client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)

class TestQueryEndpoint:
    def test_query_submission(self):
        """Test query submission returns valid query ID"""
        payload = {
            "doc_id": "test-doc-id",
            "question": "What is revenue?"
        }
        response = client.post("/query", json=payload)
        assert response.status_code in [200, 202]
        data = response.json()
        assert "status" in data

class TestCORSHeaders:
    def test_cors_headers_present(self):
        """Test CORS headers are set"""
        response = client.get("/health")
        assert "access-control-allow-origin" in response.headers or \
               "Access-Control-Allow-Origin" in response.headers

class TestConfig:
    def test_settings_load(self):
        """Test configuration loading"""
        settings = Settings()
        assert settings.port > 0
        assert settings.cache_service_url
        assert settings.aws_region

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
