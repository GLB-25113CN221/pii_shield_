"""Context reviewer: local LLM decision with honest heuristic fallback."""
import json, os, urllib.request
from urllib.parse import urlparse
from config import OLLAMA_URL, OLLAMA_MODEL

def review(text, finding):
    url=os.getenv("OLLAMA_URL",OLLAMA_URL).rstrip("/")
    if urlparse(url).hostname not in {"127.0.0.1","localhost","::1"}:
        raise RuntimeError("For privacy, Ollama must use a localhost URL.")
    lo=max(0,finding.start-100); hi=min(len(text),finding.end+100); context=text[lo:hi]
    payload={"model":os.getenv("OLLAMA_MODEL",OLLAMA_MODEL),"stream":False,"format":"json","messages":[{"role":"system","content":"Classify candidate PII from surrounding context. Return JSON {decision:'redact'|'reject'|'review',confidence:0..1,reason:'one line'}. Do not repeat the value."},{"role":"user","content":json.dumps({"type":finding.pii_type,"context":context,"candidate":finding.value})}]}
    req=urllib.request.Request(url+"/api/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=12) as r: ans=json.loads(r.read()).get("message",{}).get("content","{}")
    out=json.loads(ans); return {"decision":out.get("decision","review"),"confidence":float(out.get("confidence",.5)),"reason":str(out.get("reason","Context review"))[:180]}
