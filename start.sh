#!/bin/bash
# Start script for Render deployment

echo "🚀 Starting RAG Backend API..."
echo "📍 PORT: $PORT"
echo "🔧 Render Environment: $RENDER"

# Use PORT from environment, default to 10000 if not set
if [ -z "$PORT" ]; then
    echo "⚠️ PORT not set, using default 10000"
    PORT=10000
fi

echo "🌐 Binding to 0.0.0.0:$PORT"

# Start the application
exec python app2.py
