#!/bin/bash

# Run linters and code quality checks
echo "🔍 Running code quality checks..."

echo "📊 Running flake8..."
uv run flake8 backend/ main.py || true

echo "🔍 Checking import order with isort..."
uv run isort --check-only . || true

echo "🎨 Checking code format with black..."
uv run black --check . || true

echo "✅ Code quality checks complete!"
