#!/bin/bash

# Format Python code with isort and black
echo "🔧 Running code formatters..."

echo "📦 Running isort..."
uv run isort .

echo "🎨 Running black..."
uv run black .

echo "✅ Code formatting complete!"
