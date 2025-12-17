"""
Tests for AIGenerator to verify tool calling functionality.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, MagicMock, patch
from ai_generator import AIGenerator


class TestAIGeneratorToolCalling(unittest.TestCase):
    """Test AIGenerator's ability to call tools correctly"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.model = "claude-sonnet-4-20250514"

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_without_tools(self, mock_anthropic_class):
        """Test basic response generation without tools"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="This is a test response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response

        # Create generator and generate response
        generator = AIGenerator(self.api_key, self.model)
        result = generator.generate_response("What is Python?")

        # Assertions
        self.assertEqual(result, "This is a test response")
        mock_client.messages.create.assert_called_once()

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_tool_use(self, mock_anthropic_class):
        """Test that tool use is handled correctly"""
        # Setup mock client
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Mock initial response with tool use
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.input = {"query": "MCP servers"}
        mock_tool_block.id = "tool_123"

        mock_initial_response = Mock()
        mock_initial_response.content = [mock_tool_block]
        mock_initial_response.stop_reason = "tool_use"

        # Mock final response after tool execution
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="MCP servers are used for...")]

        mock_client.messages.create.side_effect = [
            mock_initial_response,
            mock_final_response
        ]

        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "[Course MCP]\nMCP servers enable..."

        # Create generator and generate response
        generator = AIGenerator(self.api_key, self.model)
        tools = [{"name": "search_course_content", "description": "Search courses"}]

        result = generator.generate_response(
            "What are MCP servers?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Assertions
        self.assertEqual(result, "MCP servers are used for...")
        self.assertEqual(mock_client.messages.create.call_count, 2)
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="MCP servers"
        )

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_choice_auto_added(self, mock_anthropic_class):
        """Test that tool_choice: auto is added when tools are provided"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(self.api_key, self.model)
        tools = [{"name": "test_tool", "description": "Test"}]

        generator.generate_response("Test query", tools=tools)

        # Check that tool_choice was added
        call_kwargs = mock_client.messages.create.call_args[1]
        self.assertIn("tool_choice", call_kwargs)
        self.assertEqual(call_kwargs["tool_choice"], {"type": "auto"})

    @patch('ai_generator.anthropic.Anthropic')
    def test_conversation_history_included(self, mock_anthropic_class):
        """Test that conversation history is included in system prompt"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response with context")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(self.api_key, self.model)
        history = "User: Previous question\nAssistant: Previous answer"

        generator.generate_response("Follow-up question", conversation_history=history)

        # Check that history was included in system content
        call_kwargs = mock_client.messages.create.call_args[1]
        self.assertIn("system", call_kwargs)
        self.assertIn("Previous conversation", call_kwargs["system"])
        self.assertIn(history, call_kwargs["system"])

    @patch('ai_generator.anthropic.Anthropic')
    def test_multiple_tool_results(self, mock_anthropic_class):
        """Test handling multiple tool calls in one response"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Mock multiple tool blocks
        tool_block_1 = Mock()
        tool_block_1.type = "tool_use"
        tool_block_1.name = "search_course_content"
        tool_block_1.input = {"query": "test1"}
        tool_block_1.id = "tool_1"

        tool_block_2 = Mock()
        tool_block_2.type = "tool_use"
        tool_block_2.name = "search_course_content"
        tool_block_2.input = {"query": "test2"}
        tool_block_2.id = "tool_2"

        mock_initial_response = Mock()
        mock_initial_response.content = [tool_block_1, tool_block_2]
        mock_initial_response.stop_reason = "tool_use"

        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Combined results")]

        mock_client.messages.create.side_effect = [
            mock_initial_response,
            mock_final_response
        ]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

        generator = AIGenerator(self.api_key, self.model)
        tools = [{"name": "search_course_content"}]

        result = generator.generate_response(
            "Test",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Should execute both tools
        self.assertEqual(mock_tool_manager.execute_tool.call_count, 2)

    @patch('ai_generator.anthropic.Anthropic')
    def test_sequential_tool_calling_two_rounds(self, mock_anthropic_class):
        """Test Claude makes two sequential tool calls across separate rounds"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Round 1: tool_use
        tool_block_1 = Mock()
        tool_block_1.type = "tool_use"
        tool_block_1.name = "search_course_content"
        tool_block_1.input = {"query": "lesson 2"}
        tool_block_1.id = "tool_1"
        response_1 = Mock(content=[tool_block_1], stop_reason="tool_use")

        # Round 2: tool_use (after seeing round 1 results)
        tool_block_2 = Mock()
        tool_block_2.type = "tool_use"
        tool_block_2.name = "search_course_content"
        tool_block_2.input = {"query": "lesson 5"}
        tool_block_2.id = "tool_2"
        response_2 = Mock(content=[tool_block_2], stop_reason="tool_use")

        # Final: end_turn
        response_3 = Mock(content=[Mock(text="Comparison of lessons")], stop_reason="end_turn")

        # Queue responses
        mock_client.messages.create.side_effect = [response_1, response_2, response_3]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = [
            "[Course X Lesson 2] Content...",
            "[Course X Lesson 5] Content..."
        ]

        generator = AIGenerator(self.api_key, self.model)
        result = generator.generate_response(
            "Compare lesson 2 and 5",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify: 3 API calls, 2 tool executions
        self.assertEqual(mock_client.messages.create.call_count, 3)
        self.assertEqual(mock_tool_manager.execute_tool.call_count, 2)
        self.assertEqual(result, "Comparison of lessons")

    @patch('ai_generator.anthropic.Anthropic')
    def test_sequential_stops_at_end_turn(self, mock_anthropic_class):
        """Test loop exits early when Claude signals end_turn after first round"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Round 1: tool_use
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "search_course_content"
        tool_block.input = {"query": "test"}
        tool_block.id = "tool_1"
        response_1 = Mock(content=[tool_block], stop_reason="tool_use")

        # Round 2: end_turn (no more tools needed)
        response_2 = Mock(content=[Mock(text="Final answer")], stop_reason="end_turn")

        mock_client.messages.create.side_effect = [response_1, response_2]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Search result"

        generator = AIGenerator(self.api_key, self.model)
        result = generator.generate_response(
            "Test query",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Should only make 2 API calls (not 3)
        self.assertEqual(mock_client.messages.create.call_count, 2)
        self.assertEqual(mock_tool_manager.execute_tool.call_count, 1)
        self.assertEqual(result, "Final answer")

    @patch('ai_generator.anthropic.Anthropic')
    def test_max_rounds_enforced(self, mock_anthropic_class):
        """Test that max 2 rounds enforced even if Claude wants more"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Mock 3 tool_use responses (Claude keeps wanting tools)
        tool_block_1 = Mock(type="tool_use", name="search_course_content",
                           input={"query": "q1"}, id="tool_1")
        tool_block_2 = Mock(type="tool_use", name="search_course_content",
                           input={"query": "q2"}, id="tool_2")

        response_1 = Mock(content=[tool_block_1], stop_reason="tool_use")
        response_2 = Mock(content=[tool_block_2], stop_reason="tool_use")

        # Final call should be without tools, forcing end_turn
        response_3 = Mock(content=[Mock(text="Forced final answer")], stop_reason="end_turn")

        mock_client.messages.create.side_effect = [response_1, response_2, response_3]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

        generator = AIGenerator(self.api_key, self.model)
        result = generator.generate_response(
            "Test",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify exactly 3 API calls (2 rounds + 1 final without tools)
        self.assertEqual(mock_client.messages.create.call_count, 3)
        self.assertEqual(mock_tool_manager.execute_tool.call_count, 2)

        # Verify 3rd call does NOT include tools parameter
        third_call_kwargs = mock_client.messages.create.call_args_list[2][1]
        self.assertNotIn("tools", third_call_kwargs)

        self.assertEqual(result, "Forced final answer")


if __name__ == '__main__':
    unittest.main()
