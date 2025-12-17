"""
Shared test fixtures for the RAG system test suite.

This module provides pytest fixtures for mocking components and setting up
test data used across multiple test files.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any


@pytest.fixture
def mock_vector_store():
    """Provides a mock VectorStore for testing"""
    mock_store = Mock()
    mock_store.get_existing_course_titles.return_value = []

    # Mock search results structure
    from vector_store import SearchResults
    mock_search_results = SearchResults(
        documents=["Sample course content about MCP servers..."],
        metadata=[{
            'course_title': 'Introduction to MCP',
            'lesson_number': 1
        }],
        distances=[0.3],
        error=None
    )
    mock_store.search.return_value = mock_search_results
    mock_store.get_lesson_link.return_value = "https://example.com/lesson1"

    return mock_store


@pytest.fixture
def mock_ai_generator():
    """Provides a mock AIGenerator for testing"""
    mock_gen = Mock()
    mock_gen.generate_response.return_value = "This is a test response from the AI."
    return mock_gen


@pytest.fixture
def sample_course_data():
    """Provides sample course data for testing"""
    return {
        'title': 'Introduction to MCP',
        'course_link': 'https://example.com/course',
        'instructor': 'Test Instructor',
        'lessons': [
            {
                'lesson_number': 1,
                'lesson_title': 'Getting Started with MCP',
                'lesson_link': 'https://example.com/lesson1'
            },
            {
                'lesson_number': 2,
                'lesson_title': 'Advanced MCP Concepts',
                'lesson_link': 'https://example.com/lesson2'
            }
        ]
    }


@pytest.fixture
def sample_query_request():
    """Provides a sample query request for API testing"""
    return {
        "query": "What are MCP servers?",
        "session_id": None
    }


@pytest.fixture
def sample_query_response():
    """Provides a sample query response for API testing"""
    return {
        "answer": "MCP servers enable bidirectional communication between AI and external tools.",
        "sources": [
            {"text": "Introduction to MCP - Lesson 1", "url": "https://example.com/lesson1"}
        ],
        "session_id": "test-session-123"
    }


@pytest.fixture
def mock_rag_system(mock_vector_store, mock_ai_generator):
    """Provides a mock RAGSystem with mocked dependencies"""
    with pytest.mock.patch('rag_system.VectorStore', return_value=mock_vector_store), \
         pytest.mock.patch('rag_system.AIGenerator', return_value=mock_ai_generator):
        from rag_system import RAGSystem
        from config import config
        rag = RAGSystem(config)
        return rag


@pytest.fixture
def mock_anthropic_client():
    """Provides a mock Anthropic API client"""
    mock_client = Mock()

    # Mock basic response
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response")]
    mock_response.stop_reason = "end_turn"
    mock_client.messages.create.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_tool_use_response():
    """Provides a mock response with tool use"""
    mock_tool_block = Mock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.name = "search_course_content"
    mock_tool_block.input = {"query": "test query"}
    mock_tool_block.id = "tool_123"

    mock_response = Mock()
    mock_response.content = [mock_tool_block]
    mock_response.stop_reason = "tool_use"

    return mock_response


@pytest.fixture
def mock_tool_manager():
    """Provides a mock ToolManager"""
    mock_manager = Mock()
    mock_manager.execute_tool.return_value = "[Course Test] Sample content..."
    mock_manager.get_last_sources.return_value = []
    mock_manager.get_tool_definitions.return_value = [
        {
            "name": "search_course_content",
            "description": "Search for content in courses"
        }
    ]
    return mock_manager


@pytest.fixture
def test_config():
    """Provides test configuration"""
    return {
        "CHUNK_SIZE": 800,
        "CHUNK_OVERLAP": 100,
        "MAX_RESULTS": 5,
        "MAX_HISTORY": 2,
        "ANTHROPIC_MODEL": "claude-sonnet-4-20250514",
        "EMBEDDING_MODEL": "all-MiniLM-L6-v2"
    }


@pytest.fixture(autouse=True)
def suppress_warnings():
    """Suppress resource tracker warnings in tests"""
    import warnings
    warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")
