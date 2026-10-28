#!/bin/sh
# Start the local Ollama server first, then the web app.
ollama serve >/tmp/ollama.log 2>&1 &
sleep 4
exec streamlit run app.py --server.address 0.0.0.0 --server.port "${PORT:-7860}" --server.headless true --server.enableXsrfProtection false --server.enableCORS false
