"""Local Ollama reviewer. Sends only an isolated fragment (max 200 chars)."""
import os, json, urllib.request
from config import OLLAMA_URL, OLLAMA_MODEL
def review_fragment(fragment: str, pii_type: str) -> dict:
    """Return YES/NO + reason; raises on unavailable service for graceful skip."""
    safe=fragment[:200]
    prompt=("You are a privacy review classifier. Do not repeat the fragment. "
            f"Determine whether this isolated fragment is likely {pii_type}. "
            "Reply JSON only: {\"answer\":\"YES\" or \"NO\",\"reason\":\"short reason\"}.\nFragment: "+safe)
    payload=json.dumps({"model":os.getenv("OLLAMA_MODEL",OLLAMA_MODEL),"prompt":prompt,"stream":False}).encode()
    req=urllib.request.Request(os.getenv("OLLAMA_URL",OLLAMA_URL)+"/api/generate",data=payload,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=3) as response: result=json.loads(response.read())
    return json.loads(result.get("response","{}"))
