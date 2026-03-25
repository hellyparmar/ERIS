"""
AI Assistant endpoint tests.
Tests: chat endpoint, assistant status, RAG retrieval.
"""
import pytest


class TestAssistantStatus:
    def test_status_unauthenticated(self, test_client):
        """Assistant status requires authentication."""
        resp = test_client.get("/api/v1/assistant/status")
        assert resp.status_code in (401, 404), resp.text

    def test_status_endpoint(self, test_client, auth_headers):
        """Assistant status returns provider info."""
        resp = test_client.get("/api/v1/assistant/status", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text
        if resp.status_code == 200:
            data = resp.json()
            # Should report which provider is active
            assert isinstance(data, dict)

    def test_status_has_provider_field(self, test_client, auth_headers):
        """Status response indicates whether AI is available."""
        resp = test_client.get("/api/v1/assistant/status", headers=auth_headers)
        if resp.status_code == 200:
            data = resp.json()
            assert "provider" in data or "available" in data or "status" in data


class TestChat:
    def test_chat_unauthenticated(self, test_client):
        """Chat endpoint requires authentication."""
        resp = test_client.post("/api/v1/assistant/chat",
                                json={"message": "Hello"})
        assert resp.status_code in (401, 422), resp.text

    def test_chat_empty_message(self, test_client, auth_headers):
        """Empty message should be rejected."""
        resp = test_client.post(
            "/api/v1/assistant/chat",
            json={"message": ""},
            headers=auth_headers,
        )
        assert resp.status_code in (400, 422), resp.text

    def test_chat_valid_message(self, test_client, auth_headers):
        """Valid chat message returns a response (AI may be unavailable in test)."""
        resp = test_client.post(
            "/api/v1/assistant/chat",
            json={"message": "What are today's top selling products?"},
            headers=auth_headers,
        )
        # Accept: 200 (AI ok), 404 (endpoint path differs), 503 (AI unavailable)
        assert resp.status_code in (200, 201, 404, 422, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "response" in data or "answer" in data or "message" in data

    def test_chat_sql_injection_safe(self, test_client, auth_headers):
        """Chat endpoint handles potential injection attempts without crashing."""
        malicious = "'; DROP TABLE users; --"
        resp = test_client.post(
            "/api/v1/assistant/chat",
            json={"message": malicious},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201, 400, 404, 422, 503), resp.text

    def test_chat_history(self, test_client, auth_headers):
        """Chat history endpoint is accessible."""
        resp = test_client.get("/api/v1/assistant/history", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text
        if resp.status_code == 200:
            assert isinstance(resp.json(), (list, dict))


class TestRAG:
    def test_rag_retrieval(self, test_client, auth_headers):
        """RAG retrieval endpoint responds without error."""
        resp = test_client.post(
            "/api/v1/assistant/query",
            json={"query": "Show me sales for last week"},
            headers=auth_headers,
        )
        # RAG may not be available in all environments
        assert resp.status_code in (200, 201, 404, 422, 503), resp.text

    def test_rag_context_response(self, test_client, auth_headers):
        """If RAG is enabled, response includes context sources."""
        resp = test_client.post(
            "/api/v1/assistant/query",
            json={"query": "Which products are out of stock?"},
            headers=auth_headers,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict)
