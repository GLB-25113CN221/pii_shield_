# One container: Streamlit app + Tesseract OCR + Ollama (agent model baked in).
# Works as a Hugging Face Space (Docker SDK) and with `docker run -p 7860:7860`.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=7860 \
    OLLAMA_URL=http://127.0.0.1:11434 OLLAMA_MODEL=qwen2.5:3b \
    OLLAMA_MODELS=/app/ollama_models HOME=/tmp AUDIT_DB=/tmp/pii_shield_audit.sqlite3
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates zstd tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar tesseract-ocr-ben tesseract-ocr-tam tesseract-ocr-tel tesseract-ocr-guj tesseract-ocr-kan tesseract-ocr-mal tesseract-ocr-pan libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://ollama.com/install.sh | sh
WORKDIR /app
COPY requirements.txt .
# CPU-only torch keeps the image far smaller than the default CUDA build.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt
# Download the agent model at build time so the first visit is not slow.
RUN mkdir -p /app/ollama_models && (ollama serve >/tmp/ollama_build.log 2>&1 & sleep 6 && ollama pull "$OLLAMA_MODEL" && pkill ollama || true)
COPY . .
RUN chmod +x start.sh && chmod -R a+rwX /app
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/_stcore/health',timeout=3)"
CMD ["./start.sh"]
