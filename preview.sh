#!/bin/bash

# Simple script to preview README.md locally
# This script starts a local HTTP server to preview the README

echo "🚀 Starting README Preview Server..."
echo ""
echo "📝 Opening preview.html in your default browser..."
echo "🔄 The preview will auto-refresh when you save README.md"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    # Start a simple HTTP server
    python3 -m http.server 8000
elif command -v python &> /dev/null; then
    # Fallback to python
    python -m http.server 8000
else
    echo "❌ Python not found. Please install Python to use this preview script."
    echo "Alternatively, you can open preview.html directly in your browser."
    exit 1
fi


