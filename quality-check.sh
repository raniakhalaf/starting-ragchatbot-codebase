#!/bin/bash

# Run all quality checks and auto-fix issues
echo "🚀 Running full quality check and fix pipeline..."

# Format code
echo ""
echo "═══════════════════════════════════════"
echo "Step 1: Auto-formatting code"
echo "═══════════════════════════════════════"
./format.sh

# Run linters
echo ""
echo "═══════════════════════════════════════"
echo "Step 2: Running linters"
echo "═══════════════════════════════════════"
./lint.sh

echo ""
echo "═══════════════════════════════════════"
echo "✅ Quality check pipeline complete!"
echo "═══════════════════════════════════════"
