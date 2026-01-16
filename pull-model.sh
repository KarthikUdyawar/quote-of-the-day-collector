#!/bin/bash
set -e

# Start Ollama server in background
ollama serve &

echo "Waiting for Ollama to start (30 seconds)..."
sleep 30

echo "Pulling llama3.2:3b if not already present..."
ollama pull llama3.2:3b

echo "Ollama ready!"

# Keep container running
wait