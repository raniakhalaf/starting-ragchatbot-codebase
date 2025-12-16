# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Retrieval-Augmented Generation (RAG) system for querying course materials. The system uses ChromaDB for vector storage, Anthropic's Claude API for AI generation, and FastAPI for the backend API with a simple HTML/CSS/JS frontend.

## Development Commands

### Running the Application
```bash
# Quick start using the shell script
./run.sh

# Manual start
cd backend
uv run uvicorn app:app --reload --port 8000
```

### Dependency Management

**IMPORTANT**: This project uses `uv` as the package manager. Always use `uv` commands, never use `pip` directly.

```bash
# Install/sync dependencies
uv sync

# Add a new dependency
uv add package-name

# Remove a dependency
uv remove package-name

# Run Python scripts/commands
uv run python script.py
uv run uvicorn app:app
```

### Environment Setup
Create a `.env` file in the root directory with:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Architecture

### Component Flow

The RAG system follows this pipeline:
1. **Document Ingestion** → Course documents are parsed into structured Course/Lesson objects
2. **Vector Storage** → Content is chunked and stored in ChromaDB with metadata
3. **Query Processing** → User queries trigger semantic search via Claude's tool calling
4. **Response Generation** → Claude synthesizes answers from retrieved chunks with conversation context

### Core Components

**RAGSystem** (`backend/rag_system.py`):
- Main orchestrator that coordinates all components
- Manages document ingestion workflow
- Routes queries through search tools to AI generator
- Handles session management for conversation history

**VectorStore** (`backend/vector_store.py`):
- Manages two ChromaDB collections:
  - `course_catalog`: Course metadata (titles, instructors, lesson info)
  - `course_content`: Chunked course content for semantic search
- Implements semantic course name resolution (fuzzy matching on course titles)
- Supports filtering by course title and/or lesson number

**AIGenerator** (`backend/ai_generator.py`):
- Handles Claude API interactions with tool calling
- Implements agentic tool execution loop
- Manages conversation context injection
- Uses static system prompt optimized for educational content

**DocumentProcessor** (`backend/document_processor.py`):
- Parses course documents with expected format:
  ```
  Course Title: [title]
  Course Link: [url]
  Course Instructor: [name]

  Lesson 1: [title]
  Lesson Link: [url]
  [content...]
  ```
- Creates sentence-based chunks with configurable overlap
- Adds contextual prefixes to chunks (e.g., "Course X Lesson Y content: ...")

**ToolManager & CourseSearchTool** (`backend/search_tools.py`):
- Implements Anthropic tool calling interface
- CourseSearchTool exposes semantic search to Claude
- Tracks search sources for UI display
- Supports three search modes: full-text, course-filtered, lesson-filtered

**SessionManager** (`backend/session_manager.py`):
- Maintains conversation history per session
- Implements sliding window (keeps last N exchanges)
- Formats history for AI context injection

### Data Models

**Course** (`backend/models.py`):
- `title`: Used as unique identifier
- `lessons`: List of Lesson objects
- `course_link`: Optional URL
- `instructor`: Optional metadata

**Lesson**:
- `lesson_number`: Sequential integer
- `title`: Lesson name
- `lesson_link`: Optional URL

**CourseChunk**:
- `content`: Text with contextual prefix
- `course_title`: Foreign key to Course
- `lesson_number`: Foreign key to Lesson
- `chunk_index`: Position in document

### API Endpoints

**POST /api/query**:
- Request: `{query: str, session_id?: str}`
- Response: `{answer: str, sources: List[str], session_id: str}`
- Creates new session if not provided
- Returns sources from tool searches

**GET /api/courses**:
- Response: `{total_courses: int, course_titles: List[str]}`
- Returns course catalog statistics

### Configuration

All settings in `backend/config.py`:
- `CHUNK_SIZE`: 800 characters (tuned for semantic coherence)
- `CHUNK_OVERLAP`: 100 characters (prevents context loss at boundaries)
- `MAX_RESULTS`: 5 search results per query
- `MAX_HISTORY`: 2 conversation exchanges (4 messages total)
- `ANTHROPIC_MODEL`: claude-sonnet-4-20250514
- `EMBEDDING_MODEL`: all-MiniLM-L6-v2 (SentenceTransformers)

### Document Processing Details

**Chunking Strategy**:
- Sentence-based splitting (preserves semantic units)
- Respects abbreviations (Dr., Mr., etc.)
- Overlap ensures no context loss between chunks
- First chunk of each lesson gets "Lesson X content:" prefix
- Last lesson chunks get "Course X Lesson Y content:" prefix

**Course Name Resolution**:
- Vector search on course catalog for fuzzy matching
- Enables queries like "MCP" to match "Introduction to MCP"
- Returns best match (n_results=1) from course_catalog collection

### Frontend Integration

Static files served from `frontend/`:
- `index.html`: Single-page chat interface
- `script.js`: Handles API calls, session management, message rendering
- `style.css`: UI styling

FastAPI serves frontend with `DevStaticFiles` (no-cache headers for development).

## Key Design Patterns

**Tool-Based Search**: AI decides when/how to search via Anthropic tool calling (not hardcoded retrieval)

**Dual Collection Strategy**:
- Course metadata in `course_catalog` for name resolution
- Content chunks in `course_content` for semantic search
- This enables "search for X in course Y" where Y is fuzzy-matched first

**Contextual Chunking**: Prepends course/lesson info to chunks so they're self-contained in vector space

**Session-Based History**: Conversation context is session-scoped with sliding window to prevent unbounded growth

**Startup Document Loading**: FastAPI `startup_event` auto-loads docs from `../docs` folder (skips duplicates based on course titles)

## Testing with Sample Documents

Course documents should be placed in `docs/` folder. Expected format:
- Line 1: `Course Title: [name]`
- Line 2: `Course Link: [url]` (optional)
- Line 3: `Course Instructor: [name]` (optional)
- Subsequent: `Lesson N: [title]` markers followed by content

Server auto-indexes on startup and skips already-loaded courses.
