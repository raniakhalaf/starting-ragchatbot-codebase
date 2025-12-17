import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to tools for course information.

Available Tools:
1. **search_course_content** - Search within course content for specific topics or detailed information
2. **get_course_outline** - Get the complete structure of a course including course title, course link, and all lessons with their numbers, titles, and links

Tool Usage Guidelines:
- **Course outline/structure queries**: ALWAYS use get_course_outline to retrieve the complete course structure
- **Content-specific queries**: ALWAYS use search_course_content for questions about specific topics or lessons
- **When in doubt about course-related questions**: USE TOOLS FIRST before relying on general knowledge
- **You may use tools across multiple rounds** (up to 2 rounds total)
- Use tools strategically: search once, analyze results, then search again if needed
- Each round allows you to reason about previous tool results
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Response Protocol for Course Outlines:
- When returning course outlines, include:
  * Course title
  * Course link (if available)
  * Complete list of lessons with:
    - Lesson number
    - Lesson title
    - Lesson link (if available)
- Format the outline in a clear, readable structure

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without tools
- **Course-specific questions**: Use appropriate tool first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the tool results" or "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 1500  # Increased from 800 to handle comprehensive course outlines
        }
    
    def _build_system_content(self, conversation_history: Optional[str]) -> str:
        """Build system content with optional conversation history."""
        if conversation_history:
            return f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
        return self.SYSTEM_PROMPT

    def _call_api(self, messages: List[Dict], system_content: str, tools: Optional[List] = None):
        """Make API call to Claude."""
        api_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content
        }

        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        return self.client.messages.create(**api_params)

    def _execute_tools(self, response, tool_manager) -> List[Dict]:
        """Execute all tool calls in response and return tool results."""
        tool_results = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name,
                        **content_block.input
                    )
                except Exception as e:
                    tool_result = f"Error executing tool: {str(e)}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })
        return tool_results

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional multi-round tool usage.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content and initial messages
        system_content = self._build_system_content(conversation_history)
        messages = [{"role": "user", "content": query}]

        # Multi-round tool calling loop
        MAX_TOOL_ROUNDS = 2
        rounds_completed = 0

        while rounds_completed < MAX_TOOL_ROUNDS:
            # Make API call WITH tools
            response = self._call_api(messages, system_content, tools)

            # Check if Claude wants to use tools
            if response.stop_reason != "tool_use":
                # No tool use - return final response
                return response.content[0].text

            # Tool use detected
            if not tool_manager:
                # No tool manager - return what we have
                return response.content[0].text if response.content else "Error: Tool use requested but no tool manager available"

            # Add assistant's tool use to messages
            messages.append({"role": "assistant", "content": response.content})

            # Execute tools and collect results
            tool_results = self._execute_tools(response, tool_manager)

            # Add tool results as user message
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Increment round counter
            rounds_completed += 1

        # Max rounds reached - make final call WITHOUT tools
        final_response = self._call_api(messages, system_content, tools=None)
        return final_response.content[0].text