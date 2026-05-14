#!/bin/bash
echo "Cleaning Python cache files..."

# Remove __pycache__ directories
find . -type d -name "__pycache__" -print -exec rm -rf {} + 2>/dev/null

# Remove .pyc and .pyo files
find . -type f -name "*.pyc" -print -delete 2>/dev/null
find . -type f -name "*.pyo" -print -delete 2>/dev/null

echo "Done."
