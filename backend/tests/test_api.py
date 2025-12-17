"""
API endpoint tests for the RAG system FastAPI application.

Tests all API endpoints for proper request/response handling without
requiring static files or external dependencies.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional
from unittest.mock import Mock, patch, MagicMock


# Pydantic models (same as in app.py)
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None


class SourceItem(BaseModel):
    """Represents a single source citation with optional link"""
    text: str
    url: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[SourceItem]
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]


def create_test_app(mock_rag):
    """
    Create a test FastAPI app with endpoints but without static file mounting.
    This allows testing API endpoints without filesystem dependencies.

    Args:
        mock_rag: Mock RAG system to use in endpoints
    """
    app = FastAPI(title="Course Materials RAG System - Test", root_path="")

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            # Create session if not provided
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag.session_manager.create_session()

            # Process query using RAG system
            answer, sources = mock_rag.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            analytics = mock_rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    return app


@pytest.fixture
def mock_rag_for_api():
    """Provides a mock RAG system configured for API testing"""
    mock_rag = Mock()

    # Mock session manager
    mock_session_manager = Mock()
    mock_session_manager.create_session.return_value = "test-session-123"
    mock_rag.session_manager = mock_session_manager

    # Mock query method
    mock_rag.query.return_value = (
        "MCP servers enable bidirectional communication between AI and external tools.",
        [
            {"text": "Introduction to MCP - Lesson 1", "url": "https://example.com/lesson1"}
        ]
    )

    # Mock get_course_analytics
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Introduction to MCP", "Advanced Python Programming"]
    }

    return mock_rag


@pytest.fixture
def client(mock_rag_for_api):
    """Provides a FastAPI test client with mocked RAG system"""
    app = create_test_app(mock_rag_for_api)
    return TestClient(app)


@pytest.mark.api
class TestQueryEndpoint:
    """Tests for POST /api/query endpoint"""

    def test_query_without_session_id(self, client, mock_rag_for_api):
        """Test query endpoint creates session when not provided"""
        response = client.post(
            "/api/query",
            json={"query": "What are MCP servers?"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"

        # Verify session was created
        mock_rag_for_api.session_manager.create_session.assert_called_once()

    def test_query_with_session_id(self, client, mock_rag_for_api):
        """Test query endpoint uses provided session ID"""
        response = client.post(
            "/api/query",
            json={
                "query": "Follow-up question",
                "session_id": "existing-session-456"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should use provided session ID
        mock_rag_for_api.query.assert_called_once_with(
            "Follow-up question",
            "existing-session-456"
        )

    def test_query_response_structure(self, client):
        """Test query response has correct structure"""
        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)

        # Validate source structure
        if len(data["sources"]) > 0:
            source = data["sources"][0]
            assert "text" in source
            assert "url" in source

    def test_query_missing_required_field(self, client):
        """Test query endpoint rejects request without query field"""
        response = client.post(
            "/api/query",
            json={"session_id": "test"}
        )

        assert response.status_code == 422  # Validation error

    def test_query_empty_string(self, client, mock_rag_for_api):
        """Test query endpoint accepts empty query string"""
        response = client.post(
            "/api/query",
            json={"query": ""}
        )

        # Should be processed even if empty
        assert response.status_code == 200

    def test_query_error_handling(self, client, mock_rag_for_api):
        """Test query endpoint handles RAG system errors"""
        # Make the query method raise an exception
        mock_rag_for_api.query.side_effect = Exception("Database connection failed")

        response = client.post(
            "/api/query",
            json={"query": "Test"}
        )

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    def test_query_with_sources(self, client, mock_rag_for_api):
        """Test query response includes sources correctly"""
        mock_rag_for_api.query.return_value = (
            "Test answer",
            [
                {"text": "Course A - Lesson 1", "url": "https://example.com/a1"},
                {"text": "Course B - Lesson 2", "url": None}
            ]
        )

        response = client.post(
            "/api/query",
            json={"query": "Test"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) == 2
        assert data["sources"][0]["text"] == "Course A - Lesson 1"
        assert data["sources"][0]["url"] == "https://example.com/a1"
        assert data["sources"][1]["url"] is None


@pytest.mark.api
class TestCoursesEndpoint:
    """Tests for GET /api/courses endpoint"""

    def test_get_courses_success(self, client, mock_rag_for_api):
        """Test courses endpoint returns course statistics"""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 2
        assert len(data["course_titles"]) == 2

    def test_get_courses_response_structure(self, client):
        """Test courses response has correct structure"""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert all(isinstance(title, str) for title in data["course_titles"])

    def test_get_courses_empty_catalog(self, client, mock_rag_for_api):
        """Test courses endpoint with empty course catalog"""
        mock_rag_for_api.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_get_courses_error_handling(self, client, mock_rag_for_api):
        """Test courses endpoint handles errors"""
        mock_rag_for_api.get_course_analytics.side_effect = Exception("Vector store error")

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert "Vector store error" in response.json()["detail"]

    def test_get_courses_large_catalog(self, client, mock_rag_for_api):
        """Test courses endpoint with many courses"""
        mock_titles = [f"Course {i}" for i in range(100)]
        mock_rag_for_api.get_course_analytics.return_value = {
            "total_courses": 100,
            "course_titles": mock_titles
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 100
        assert len(data["course_titles"]) == 100


@pytest.mark.api
class TestAPIIntegration:
    """Integration tests for API workflows"""

    def test_query_then_courses(self, client, mock_rag_for_api):
        """Test sequential API calls work correctly"""
        # First query
        query_response = client.post(
            "/api/query",
            json={"query": "What courses are available?"}
        )
        assert query_response.status_code == 200

        # Then get courses
        courses_response = client.get("/api/courses")
        assert courses_response.status_code == 200

    def test_multiple_queries_same_session(self, client, mock_rag_for_api):
        """Test multiple queries using the same session"""
        # First query creates session
        response1 = client.post(
            "/api/query",
            json={"query": "First question"}
        )
        session_id = response1.json()["session_id"]

        # Second query uses same session
        response2 = client.post(
            "/api/query",
            json={
                "query": "Follow-up question",
                "session_id": session_id
            }
        )

        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

    def test_cors_headers_not_present_in_test(self, client):
        """Test that we're testing core functionality without CORS complexity"""
        # In test environment, we don't need CORS middleware
        # This test just confirms our test app works without it
        response = client.get("/api/courses")
        assert response.status_code == 200

    def test_content_type_json(self, client):
        """Test API returns JSON content type"""
        response = client.post(
            "/api/query",
            json={"query": "Test"}
        )

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


@pytest.mark.api
class TestRequestValidation:
    """Tests for request validation and edge cases"""

    def test_query_with_extra_fields(self, client):
        """Test query endpoint ignores extra fields"""
        response = client.post(
            "/api/query",
            json={
                "query": "Test",
                "extra_field": "should be ignored",
                "another_field": 123
            }
        )

        # Should succeed and ignore extra fields
        assert response.status_code == 200

    def test_query_with_null_session_id(self, client):
        """Test query with explicit null session_id"""
        response = client.post(
            "/api/query",
            json={
                "query": "Test",
                "session_id": None
            }
        )

        assert response.status_code == 200
        # Should create new session
        assert response.json()["session_id"] is not None

    def test_query_with_very_long_query(self, client, mock_rag_for_api):
        """Test query with very long text"""
        long_query = "What is MCP? " * 1000  # Very long query
        response = client.post(
            "/api/query",
            json={"query": long_query}
        )

        assert response.status_code == 200

    def test_invalid_json_body(self, client):
        """Test API rejects invalid JSON"""
        response = client.post(
            "/api/query",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_get_request_to_query_endpoint(self, client):
        """Test GET request to POST-only endpoint"""
        response = client.get("/api/query")

        assert response.status_code == 405  # Method not allowed

    def test_post_request_to_courses_endpoint(self, client):
        """Test POST request to GET-only endpoint"""
        response = client.post("/api/courses", json={})

        assert response.status_code == 405  # Method not allowed


if __name__ == '__main__':
    pytest.main([__file__, "-v"])
