"""PII Shield configuration. Assumption: local-first demo; review legal obligations with counsel."""
import os
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "20"))
BLOCK_HIGH_RISK_FIELDS = os.getenv("BLOCK_HIGH_RISK_FIELDS", "false").lower() == "true"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
AUDIT_DB = os.getenv("AUDIT_DB", "pii_shield_audit.sqlite3")
AUDIT_RETENTION_DAYS = 365
MAX_VERIFY_ITERATIONS = 3
SUPPORTED_LANGUAGES = ["Auto-detect","English","Hindi","Marathi","Bengali","Tamil","Telugu","Gujarati","Kannada","Malayalam","Punjabi"]
