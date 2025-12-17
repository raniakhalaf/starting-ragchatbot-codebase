"""
Tests for CourseSearchTool to verify proper execution and output formatting.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, MagicMock
from search_tools import CourseSearchTool
from vector_store import SearchResults


class TestCourseSearchTool(unittest.TestCase):
    """Test CourseSearchTool execute method and output formatting"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock vector store
        self.mock_vector_store = Mock()
        self.tool = CourseSearchTool(self.mock_vector_store)

    def test_execute_with_valid_results(self):
        """Test execute method returns properly formatted results"""
        # Mock search results
        mock_results = SearchResults(
            documents=["This is lesson content about MCP servers."],
            metadata=[{
                'course_title': 'MCP: Build Rich-Context AI Apps with Anthropic',
                'lesson_number': 1
            }],
            distances=[0.5],
            error=None
        )
        self.mock_vector_store.search.return_value = mock_results
        self.mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"

        # Execute search
        result = self.tool.execute(query="MCP servers")

        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn("MCP: Build Rich-Context AI Apps with Anthropic", result)
        self.assertIn("Lesson 1", result)
        self.assertIn("lesson content about MCP servers", result)

        # Verify search was called correctly
        self.mock_vector_store.search.assert_called_once_with(
            query="MCP servers",
            course_name=None,
            lesson_number=None
        )

    def test_execute_with_course_filter(self):
        """Test execute with course name filter"""
        mock_results = SearchResults(
            documents=["Content about lesson 5"],
            metadata=[{
                'course_title': 'MCP: Build Rich-Context AI Apps with Anthropic',
                'lesson_number': 5
            }],
            distances=[0.3],
            error=None
        )
        self.mock_vector_store.search.return_value = mock_results
        self.mock_vector_store.get_lesson_link.return_value = None

        result = self.tool.execute(
            query="tool calling",
            course_name="MCP"
        )

        self.assertIsInstance(result, str)
        self.mock_vector_store.search.assert_called_once_with(
            query="tool calling",
            course_name="MCP",
            lesson_number=None
        )

    def test_execute_with_empty_results(self):
        """Test execute returns proper message when no results found"""
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        self.mock_vector_store.search.return_value = mock_results

        result = self.tool.execute(query="nonexistent topic")

        self.assertIn("No relevant content found", result)

    def test_execute_with_error(self):
        """Test execute handles search errors properly"""
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error="ChromaDB connection error"
        )
        self.mock_vector_store.search.return_value = mock_results

        result = self.tool.execute(query="test query")

        self.assertEqual(result, "ChromaDB connection error")

    def test_last_sources_populated(self):
        """Test that last_sources is populated with URLs"""
        mock_results = SearchResults(
            documents=["Content 1", "Content 2"],
            metadata=[
                {'course_title': 'Course A', 'lesson_number': 1},
                {'course_title': 'Course A', 'lesson_number': 2}
            ],
            distances=[0.4, 0.6],
            error=None
        )
        self.mock_vector_store.search.return_value = mock_results
        self.mock_vector_store.get_lesson_link.side_effect = [
            "https://example.com/lesson1",
            "https://example.com/lesson2"
        ]

        self.tool.execute(query="test")

        # Verify last_sources has correct structure
        self.assertEqual(len(self.tool.last_sources), 2)
        self.assertIsInstance(self.tool.last_sources[0], dict)
        self.assertIn('text', self.tool.last_sources[0])
        self.assertIn('url', self.tool.last_sources[0])
        self.assertEqual(self.tool.last_sources[0]['text'], 'Course A - Lesson 1')
        self.assertEqual(self.tool.last_sources[0]['url'], 'https://example.com/lesson1')

    def test_last_sources_with_none_urls(self):
        """Test last_sources handles None URLs correctly"""
        mock_results = SearchResults(
            documents=["Content"],
            metadata=[{'course_title': 'Course B', 'lesson_number': 3}],
            distances=[0.2],
            error=None
        )
        self.mock_vector_store.search.return_value = mock_results
        self.mock_vector_store.get_lesson_link.return_value = None

        self.tool.execute(query="test")

        self.assertEqual(len(self.tool.last_sources), 1)
        self.assertIsNone(self.tool.last_sources[0]['url'])

    def test_format_results_structure(self):
        """Test _format_results produces correct structure"""
        mock_results = SearchResults(
            documents=["Sample content"],
            metadata=[{'course_title': 'Test Course', 'lesson_number': None}],
            distances=[0.1],
            error=None
        )
        self.mock_vector_store.search.return_value = mock_results

        result = self.tool.execute(query="test")

        # Should have course title in brackets
        self.assertIn("[Test Course]", result)
        self.assertIn("Sample content", result)


if __name__ == '__main__':
    unittest.main()
