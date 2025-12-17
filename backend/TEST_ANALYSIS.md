# RAG System Test Analysis & Findings

## Test Suite Summary

**Total Tests**: 19
**Status**: ✅ All Passing
**Test Coverage**:
- CourseSearchTool execution: 7 tests
- AIGenerator tool calling: 5 tests
- RAG system integration: 7 tests

## Key Findings

### 1. ✅ CourseSearchTool is Working Correctly

**Tests Passed**:
- ✓ Returns properly formatted results with course and lesson context
- ✓ Handles course name filtering correctly
- ✓ Returns appropriate error messages for empty results
- ✓ Handles search errors gracefully
- ✓ Populates `last_sources` with correct structure (text + URL)
- ✓ Handles None URLs correctly

**Conclusion**: The CourseSearchTool implementation is solid and functioning as expected.

### 2. ✅ AIGenerator Tool Calling is Working Correctly

**Tests Passed**:
- ✓ Generates responses without tools
- ✓ Handles tool use correctly (two-stage API call)
- ✓ Adds `tool_choice: auto` when tools are provided
- ✓ Includes conversation history in system prompt
- ✓ Handles multiple tool calls in single response

**Conclusion**: The AIGenerator correctly implements Anthropic's tool calling protocol.

### 3. ✅ RAG System Integration is Working Correctly

**Tests Passed**:
- ✓ Queries trigger search tool appropriately
- ✓ Sources are returned from searches
- ✓ Session management maintains conversation history
- ✓ Both search and outline tools are registered
- ✓ Sources are reset after each query
- ✓ Content query flow works end-to-end
- ✓ Outline query flow works end-to-end

**Conclusion**: The RAG system orchestrates all components correctly.

## Potential Issues Identified

While all unit tests pass, the tests reveal potential real-world failure points:

### Issue 1: Missing Error Handling in Production

**Problem**: Tests use mocks that always return valid data. In production:
- ChromaDB might be unavailable
- API keys might be invalid
- Network timeouts could occur

**Recommendation**: Add error handling and retry logic to:
- `vector_store.py` - Wrap ChromaDB calls in try-catch
- `ai_generator.py` - Handle Anthropic API errors
- `rag_system.py` - Gracefully degrade when components fail

### Issue 2: AI Generator Max Tokens May Be Too Low

**Current Setting**: `max_tokens: 800`

**Problem**: For course outline queries with many lessons, 800 tokens might be insufficient to return:
- Course title
- Course link
- All lesson numbers, titles, and links

**Recommendation**: Increase `max_tokens` to 1500-2000 for outline-heavy responses.

**Location**: `backend/ai_generator.py`, line 40

### Issue 3: No Validation for Tool Inputs

**Problem**: The AIGenerator passes tool inputs directly to tools without validation.

**Risk**:
- Invalid course titles could cause errors
- Missing required parameters might crash tools
- Malformed data from AI could propagate

**Recommendation**: Add input validation in tool `execute()` methods.

### Issue 4: System Prompt May Cause AI to Not Use Tools

**Current Prompt** (lines 8-45 in `ai_generator.py`):
```
- **One tool call per query maximum**
- **General knowledge questions**: Answer using existing knowledge without tools
```

**Problem**: The AI might choose NOT to use tools when it should, especially for:
- Ambiguous queries that could be answered from general knowledge
- Follow-up questions where context isn't clear

**Recommendation**: Make the prompt more aggressive about tool usage for course-related queries.

### Issue 5: Sources May Not Display for Outline Queries

**Problem**: `CourseOutlineTool` doesn't set `last_sources` attribute.

**Result**: When users ask for course outlines, no source links appear in the UI.

**Fix Required**: Add `last_sources` tracking to `CourseOutlineTool`.

## Recommended Fixes

### Priority 1: Fix CourseOutlineTool Sources (CRITICAL)

The `CourseOutlineTool` doesn't track sources for the UI. Add this capability:

```python
# In backend/search_tools.py, CourseOutlineTool class

def __init__(self, vector_store: VectorStore):
    self.store = vector_store
    self.last_sources = []  # Add this line

def execute(self, course_title: str) -> str:
    # ... existing code ...

    # Before returning, set last_sources
    if metadata:
        course_link = metadata.get('course_link')
        self.last_sources = [{
            "text": course_title,
            "url": course_link
        }]
    else:
        self.last_sources = []

    return self._format_outline(metadata)
```

### Priority 2: Increase Max Tokens

```python
# In backend/ai_generator.py, line 40
self.base_params = {
    "model": self.model,
    "temperature": 0,
    "max_tokens": 1500  # Increased from 800
}
```

### Priority 3: Improve System Prompt

```python
# In backend/ai_generator.py, modify SYSTEM_PROMPT

Tool Usage Guidelines:
- **Course outline/structure queries**: ALWAYS use get_course_outline
- **Content-specific queries**: ALWAYS use search_course_content
- **One tool call per query maximum**
- When in doubt about course-related queries, USE TOOLS FIRST
```

### Priority 4: Add Error Handling

```python
# In backend/rag_system.py, query method

def query(self, query: str, session_id: Optional[str] = None) -> Tuple[str, List[str]]:
    try:
        # ... existing code ...
        response = self.ai_generator.generate_response(...)
        sources = self.tool_manager.get_last_sources()

        # ... existing code ...
        return response, sources

    except Exception as e:
        print(f"Error processing query: {e}")
        # Return graceful error message
        error_msg = "I'm having trouble processing your request. Please try again."
        return error_msg, []
```

## Test Execution Instructions

To run the tests:

```bash
cd backend
uv run python -m unittest discover -s tests -p "test_*.py" -v
```

## Conclusion

**Current Status**: All core components are functioning correctly in isolation.

**Why RAG might be failing**: The failures are likely due to:
1. ❌ CourseOutlineTool not providing sources to UI
2. ❌ max_tokens too low for comprehensive responses
3. ❌ System prompt not aggressive enough about tool usage
4. ❌ Missing error handling for production edge cases

**Next Steps**: Implement the Priority 1-4 fixes above to resolve production failures.
