# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.


## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- Node.js and npm (for frontend development tools)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Install Node.js dependencies** (for development tools)
   ```bash
   npm install
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Code Quality Tools

This project includes automated code quality tools for both Python backend and frontend code.

### Running Quality Checks

**Quick quality check (format + lint):**
```bash
./quality-check.sh
```

**Format code only:**
```bash
# Python backend
./format.sh

# Frontend (HTML/CSS/JS)
npm run format
```

**Lint code only (no modifications):**
```bash
# Python backend
./lint.sh

# Frontend
npm run format:check
```

### Tools Used

**Backend (Python):**
- **Black**: Code formatter
- **isort**: Import statement organizer
- **flake8**: Style guide enforcement

**Frontend (JavaScript/CSS/HTML):**
- **Prettier**: Code formatter

For detailed information about code quality tools and configuration, see [frontend-changes.md](./frontend-changes.md).

