# Development Infrastructure Documentation

This document outlines the code quality tools, testing infrastructure, and improvements added to the RAG chatbot development workflow.

---

# Part 1: Code Quality Implementation

## Overview

Essential code quality tools have been integrated into the development workflow to ensure consistent formatting and maintain code quality across both frontend and backend code.

## Tools Added

### Backend (Python)
- **Black** (v25.12.0+): Automatic code formatter for Python
- **isort** (v7.0.0+): Import statement organizer
- **flake8** (v7.3.0+): Style guide enforcement and linting

### Frontend (JavaScript/CSS/HTML)
- **Prettier** (v3.1.1): Automatic code formatter for frontend files

## Configuration Files

### 1. pyproject.toml
Added tool configurations for Python quality tools:
- **Black configuration**: 88 character line length, Python 3.13 target
- **isort configuration**: Black-compatible profile with consistent import formatting
- **flake8 configuration**: Relaxed line length to match Black (88 chars)

### 2. .prettierrc
Frontend code formatting rules:
```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
```

### 3. .prettierignore
Excludes build artifacts and dependencies from formatting.

### 4. package.json
New file for frontend tooling with npm scripts:
- `npm run format`: Auto-format all frontend files
- `npm run format:check`: Check frontend formatting without modifying
- `npm run lint`: Validate frontend code formatting

## Development Scripts

Three bash scripts have been created for easy quality checks:

### 1. format.sh
Automatically formats all Python code:
```bash
./format.sh
```
Runs:
- isort (import sorting)
- black (code formatting)

### 2. lint.sh
Checks code quality without modifying files:
```bash
./lint.sh
```
Runs:
- flake8 (linting)
- isort --check-only (import order validation)
- black --check (format validation)

### 3. quality-check.sh
Complete quality pipeline (format + lint):
```bash
./quality-check.sh
```
Runs both formatting and linting in sequence.

## Changes Made to Existing Code

### Python Backend
All Python files have been automatically formatted with Black and isort:
- `backend/ai_generator.py`
- `backend/app.py`
- `backend/config.py`
- `backend/document_processor.py`
- `backend/models.py`
- `backend/rag_system.py`
- `backend/search_tools.py`
- `backend/session_manager.py`
- `backend/vector_store.py`
- `main.py`

Changes include:
- Consistent import ordering
- Standardized line lengths (88 characters)
- Proper spacing around operators and functions
- Consistent quote usage

### Frontend Files
All frontend files have been formatted with Prettier:
- `frontend/index.html`
- `frontend/script.js`
- `frontend/style.css`

Changes include:
- Consistent indentation (2 spaces)
- Single quotes for JavaScript strings
- Proper trailing commas in ES5 contexts
- Consistent line breaks

## Usage Guide

### For Python Development

**Before committing code:**
```bash
# Auto-format your code
./format.sh

# Or run full quality check
./quality-check.sh
```

**Check code quality only (no modifications):**
```bash
./lint.sh
```

**Using uv directly:**
```bash
# Format code
uv run black .
uv run isort .

# Check code quality
uv run flake8 backend/ main.py
uv run black --check .
uv run isort --check-only .
```

### For Frontend Development

**Format frontend files:**
```bash
npm run format
```

**Check frontend formatting:**
```bash
npm run format:check
# or
npm run lint
```

## Dependencies Added

### Python (via uv)
Added to `[dependency-groups.dev]` in pyproject.toml:
- black>=25.12.0
- flake8>=7.3.0
- isort>=7.0.0

Install with:
```bash
uv sync
```

### Node.js (via npm)
Added to package.json:
- prettier@^3.1.1

Install with:
```bash
npm install
```

## Updated .gitignore

Added entries to ignore:
- `node_modules/` - npm dependencies
- `npm-debug.log*` - npm error logs
- `yarn-debug.log*` - yarn logs
- `yarn-error.log*` - yarn error logs
- `package-lock.json` - npm lock file

## Benefits

1. **Consistency**: All code follows the same formatting standards
2. **Reduced Code Review Time**: No need to discuss formatting preferences
3. **Fewer Merge Conflicts**: Consistent formatting reduces git conflicts
4. **Better Readability**: Standardized code is easier to read and understand
5. **Automated Quality**: Tools catch potential issues before manual review

## Integration with Development Workflow

### Recommended Workflow

1. Make code changes
2. Run `./format.sh` to auto-format (or `npm run format` for frontend)
3. Run `./lint.sh` to check for issues
4. Fix any reported issues
5. Commit changes

### Pre-commit Hook (Optional)

Consider adding a git pre-commit hook to automatically format code:

```bash
#!/bin/sh
./format.sh
npm run format
```

## Troubleshooting

### "uv: command not found"
Install uv package manager first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "npm: command not found"
Install Node.js and npm from: https://nodejs.org/

### Formatting conflicts
If Black and flake8 disagree, Black takes precedence. The flake8 configuration has been adjusted to be compatible with Black's formatting decisions.

---

# Part 2: Testing Infrastructure

## Summary
This implementation focused on enhancing the **backend testing infrastructure** for the RAG system.

## Changes Made

### Backend Testing Infrastructure

#### 1. **Test Dependencies** (pyproject.toml)
- Added `pytest>=8.0.0` for modern testing framework
- Added `httpx>=0.27.0` for FastAPI TestClient support

#### 2. **Pytest Configuration** (pyproject.toml)
- Added `[tool.pytest.ini_options]` section
- Configured test discovery paths: `backend/tests`
- Set file/class/function naming patterns
- Added verbose output and short traceback options
- Defined test markers: `unit`, `integration`, `api`

#### 3. **Shared Test Fixtures** (backend/tests/conftest.py)
Created comprehensive fixtures for reusable test components:
- `mock_vector_store`: Mock VectorStore with sample search results
- `mock_ai_generator`: Mock AIGenerator with sample responses
- `sample_course_data`: Sample course metadata structure
- `sample_query_request/response`: API request/response samples
- `mock_rag_system`: Complete mock RAG system for integration tests
- `mock_anthropic_client`: Mock Anthropic API client
- `mock_tool_use_response`: Mock Claude tool calling response
- `mock_tool_manager`: Mock ToolManager for search tools
- `test_config`: Test configuration values
- `suppress_warnings`: Auto-applied fixture to silence resource tracker warnings

#### 4. **API Endpoint Tests** (backend/tests/test_api.py)
Created comprehensive test suite with 22 tests covering:

**Test App Factory:**
- `create_test_app(mock_rag)`: Creates FastAPI app without static file dependencies
- Uses closure to inject mock RAG system into endpoints
- Avoids filesystem dependencies that cause test failures

**Test Categories:**

**TestQueryEndpoint (7 tests):**
- Query without/with session ID
- Response structure validation
- Missing required fields
- Empty string handling
- Error handling
- Source citation structure

**TestCoursesEndpoint (5 tests):**
- Success response
- Response structure validation
- Empty catalog handling
- Error handling
- Large catalog stress test

**TestAPIIntegration (4 tests):**
- Sequential API call workflows
- Session persistence across queries
- CORS-free test environment
- JSON content type verification

**TestRequestValidation (6 tests):**
- Extra fields handling
- Null session ID
- Very long query strings
- Invalid JSON rejection
- HTTP method validation (GET/POST)

## Test Results

All tests passing:
- **22 API tests** (test_api.py)
- **22 existing tests** preserved (test_ai_generator.py, test_course_search_tool.py, test_rag_system.py)
- **Total: 44 tests passing**

## Usage

### Run All Tests
```bash
uv run pytest backend/tests/ -v
```

### Run Only API Tests
```bash
uv run pytest backend/tests/test_api.py -v
# Or using marker:
uv run pytest -m api -v
```

### Run Specific Test Class
```bash
uv run pytest backend/tests/test_api.py::TestQueryEndpoint -v
```

### Run With Coverage (if coverage installed)
```bash
uv run pytest backend/tests/ --cov=backend --cov-report=html
```

## Architecture Notes

**Static File Isolation:**
The test app factory (`create_test_app`) solves the static file mounting issue by:
1. Creating a separate FastAPI instance for testing
2. Defining endpoints inline with mock dependencies via closure
3. Avoiding `app.mount()` for static files
4. Injecting mock RAG system directly into endpoint functions

This approach ensures API tests run without requiring the `../frontend` directory.

**Fixture Pattern:**
Using pytest fixtures for mocking provides:
- Consistent mock behavior across tests
- Easy test data management
- Automatic cleanup
- Reduced code duplication

## Impact

This enhancement provides:
- ✅ Comprehensive API endpoint test coverage
- ✅ Organized test fixtures for maintainability
- ✅ Clean pytest configuration
- ✅ No breaking changes to existing tests
- ✅ Foundation for future test expansion

---

# Future Enhancements

Potential additions for further quality improvements:
- **mypy**: Static type checking for Python
- **ESLint**: JavaScript linting
- **Husky**: Git hooks for automatic quality checks
- **GitHub Actions**: CI/CD pipeline for automated quality checks

# Summary

This implementation establishes a solid foundation for maintaining code quality, testing infrastructure, and consistency across the RAG chatbot codebase. All tools are configured to work harmoniously together, and the provided scripts make it easy to maintain high code quality standards.
