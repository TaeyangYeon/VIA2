#!/usr/bin/env bash
set -euo pipefail

OLLAMA_URL="http://localhost:11434"
TIMEOUT=30

check_running() {
    curl -s --max-time 2 "$OLLAMA_URL" > /dev/null 2>&1
}

if check_running; then
    echo "Ollama already running at $OLLAMA_URL"
    exit 0
fi

echo "Starting ollama serve in background..."
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!
echo "PID: $OLLAMA_PID"

elapsed=0
while ! check_running; do
    if [ $elapsed -ge $TIMEOUT ]; then
        echo "ERROR: Ollama did not start within ${TIMEOUT}s"
        kill "$OLLAMA_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 1
    elapsed=$((elapsed + 1))
done

echo "Ollama is ready at $OLLAMA_URL (waited ${elapsed}s)"
