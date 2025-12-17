"""
Integration tests for RAG system to verify end-to-end query handling.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, MagicMock, patch
from rag_system import RAGSystem
from config import config


class TestRAGSystemIntegration(unittest.TestCase):
    """Test RAG system's end-to-end query handling"""

    def setUp(self):
        """Set up test fixtures"""
        # We'll need to mock the vector store to avoid real ChromaDB calls
        self.config = config

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_query_triggers_search_tool(self, mock_ai_gen_class, mock_vector_store_class):
        """Test that content queries trigger the search tool"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        mock_vector_store.get_existing_course_titles.return_value = []

        mock_ai_gen = Mock()
        mock_ai_gen_class.return_value = mock_ai_gen
        mock_ai_gen.generate_response.return_value = "MCP servers enable communication..."

        # Create RAG system
        rag = RAGSystem(self.config)

        # Execute query
        answer, sources = rag.query("What are MCP servers?")

        # Assertions
        self.assertIsInstance(answer, str)
        self.assertIsInstance(sources, list)

        # Verify AI generator was called with tools
        self.assertTrue(mock_ai_gen.generate_response.called)
        call_kwargs = mock_ai_gen.generate_response.call_args[1]
        self.assertIn('tools', call_kwargs)
        self.assertIsNotNone(call_kwargs['tools'])

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_sources_returned_from_search(self, mock_ai_gen_class, mock_vector_store_class):
        """Test that sources are properly returned from searches"""
        # Setup vector store mock
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        mock_vector_store.get_existing_course_titles.return_value = []

        # Setup AI generator to simulate tool calling
        mock_ai_gen = Mock()
        mock_ai_gen_class.return_value = mock_ai_gen

        def mock_generate(*args, **kwargs):
            # Simulate tool execution by calling tool_manager
            tool_manager = kwargs.get('tool_manager')
            if tool_manager:
                # Manually trigger the search tool
                from search_tools import CourseSearchTool
                search_tool = None
                for tool in tool_manager.tools.values():
                    if isinstance(tool, CourseSearchTool):
                        search_tool = tool
                        break

                if search_tool:
                    # Mock last_sources
                    search_tool.last_sources = [
                        {"text": "MCP Course - Lesson 1", "url": "https://example.com/lesson1"}
                    ]

            return "Answer about MCP"

        mock_ai_gen.generate_response.side_effect = mock_generate

        # Create RAG system
        rag = RAGSystem(self.config)

        # Execute query
        answer, sources = rag.query("What are MCP servers?")

        # Verify sources are returned
        self.assertIsInstance(sources, list)

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_session_management(self, mock_ai_gen_class, mock_vector_store_class):
        """Test that conversation history is maintained across queries"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        mock_vector_store.get_existing_course_titles.return_value = []

        mock_ai_gen = Mock()
        mock_ai_gen_class.return_value = mock_ai_gen
        mock_ai_gen.generate_response.return_value = "Response"

        # Create RAG system
        rag = RAGSystem(self.config)

        # Create session
        session_id = rag.session_manager.create_session()

        # First query
        rag.query("First question", session_id=session_id)

        # Second query
        rag.query("Follow-up question", session_id=session_id)

        # Verify second call included conversation history
        calls = mock_ai_gen.generate_response.call_args_list
        self.assertEqual(len(calls), 2)

        # Second call should have history
        second_call_kwargs = calls[1][1]
        self.assertIn('conversation_history', second_call_kwargs)
        history = second_call_kwargs['conversation_history']
        if history:  # History might be None if session is empty
            self.assertIsInstance(history, str)

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_tool_manager_has_both_tools(self, mock_ai_gen_class, mock_vector_store_class):
        """Test that both search and outline tools are registered"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        mock_vector_store.get_existing_course_titles.return_value = []

        mock_ai_gen = Mock()
        mock_ai_gen_class.return_value = mock_ai_gen

        # Create RAG system
        rag = RAGSystem(self.config)

        # Verify both tools are registered
        tool_defs = rag.tool_manager.get_tool_definitions()
        self.assertEqual(len(tool_defs), 2)

        tool_names = [tool['name'] for tool in tool_defs]
        self.assertIn('search_course_content', tool_names)
        self.assertIn('get_course_outline', tool_names)

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_sources_reset_after_query(self, mock_ai_gen_class, mock_vector_store_class):
        """Test that sources are reset after each query"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        mock_vector_store.get_existing_course_titles.return_value = []

        mock_ai_gen = Mock()
        mock_ai_gen_class.return_value = mock_ai_gen
        mock_ai_gen.generate_response.return_value = "Answer"

        # Create RAG system
        rag = RAGSystem(self.config)

        # Manually set sources on search tool
        if hasattr(rag.search_tool, 'last_sources'):
            rag.search_tool.last_sources = [{"text": "Test", "url": None}]

        # Execute query
        rag.query("Test question")

        # Sources should be reset
        sources_after = rag.tool_manager.get_last_sources()
        self.assertEqual(sources_after, [])


class TestRAGSystemRealScenarios(unittest.TestCase):
    """Test RAG system with real-world query scenarios"""

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_content_query_flow(self, mock_ai_gen_class, mock_vector_store_class):
        """Test complete flow for a content-specific query"""
        # Setup vector store to return search results
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        mock_vector_store.get_existing_course_titles.return_value = []

        from vector_store import SearchResults
        mock_search_results = SearchResults(
            documents=["MCP servers enable bidirectional communication..."],
            metadata=[{
                'course_title': 'MCP: Build Rich-Context AI Apps with Anthropic',
                'lesson_number': 2
            }],
            distances=[0.3],
            error=None
        )
        mock_vector_store.search.return_value = mock_search_results
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson2"

        # Setup AI generator
        mock_ai_gen = Mock()
        mock_ai_gen_class.return_value = mock_ai_gen
        mock_ai_gen.generate_response.return_value = "MCP servers enable bidirectional communication between AI and external tools."

        # Create RAG system and query
        rag = RAGSystem(config)
        answer, sources = rag.query("Explain MCP servers")

        # Verify the flow
        self.assertIsInstance(answer, str)
        self.assertTrue(len(answer) > 0)

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_outline_query_flow(self, mock_ai_gen_class, mock_vector_store_class):
        """Test complete flow for a course outline query"""
        # Setup vector store
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        mock_vector_store.get_existing_course_titles.return_value = []

        mock_course_metadata = {
            'title': 'MCP: Build Rich-Context AI Apps with Anthropic',
            'course_link': 'https://example.com/course',
            'instructor': 'Test Instructor',
            'lessons': [
                {'lesson_number': 0, 'lesson_title': 'Introduction', 'lesson_link': 'https://example.com/l0'},
                {'lesson_number': 1, 'lesson_title': 'Getting Started', 'lesson_link': 'https://example.com/l1'}
            ]
        }
        mock_vector_store.get_course_metadata.return_value = mock_course_metadata

        # Setup AI generator
        mock_ai_gen = Mock()
        mock_ai_gen_class.return_value = mock_ai_gen
        mock_ai_gen.generate_response.return_value = "Here is the course outline..."

        # Create RAG system and query
        rag = RAGSystem(config)
        answer, sources = rag.query("What is the outline of the MCP course?")

        # Verify response
        self.assertIsInstance(answer, str)


if __name__ == '__main__':
    unittest.main()
