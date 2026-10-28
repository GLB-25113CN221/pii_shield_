"""LLM-driven planner using Ollama's native tool/function-calling interface."""
import json, os, urllib.request
from urllib.parse import urlparse
from config import OLLAMA_URL, OLLAMA_MODEL
TOOLS = ["extract_text", "ocr_page", "rasterize_pdf", "detect_identifiers", "detect_names_addresses", "validate_candidate", "redact_text", "redact_image_boxes", "redact_pdf", "redact_docx", "verify_output"]
DESCRIPTIONS={
 "extract_text":"Extract text from the current document payload.","ocr_page":"OCR a raster page and return text with word boxes and confidence.","rasterize_pdf":"Rasterize PDF pages for scanned-document inspection.","detect_identifiers":"Find Indian identifier candidates using patterns and checksums.","detect_names_addresses":"Find possible names and addresses using multilingual NER and label heuristics.","validate_candidate":"Ask the context reviewer to assess ambiguous findings.","redact_text":"Redact accepted findings in text.","redact_image_boxes":"Mask image regions identified as sensitive.","redact_pdf":"Redact text-layer PDF content.","redact_docx":"Redact DOCX paragraphs, tables, headers and footers.","verify_output":"Run a red-team residual-PII check on output."
}
def _tool_schema(name):
    return {"type":"function","function":{"name":name,"description":DESCRIPTIONS[name],"parameters":{"type":"object","properties":{"reason":{"type":"string","description":"Brief reason this tool is needed, without any PII"}},"required":[]}}}
def _local_base_url():
    url=os.getenv("OLLAMA_URL",OLLAMA_URL).rstrip("/")
    host=urlparse(url).hostname
    if host not in {"127.0.0.1","localhost","::1"}:
        raise RuntimeError("For privacy, Ollama must use a localhost URL.")
    return url

def ollama_available():
    try:
        req=urllib.request.Request(_local_base_url()+"/api/tags")
        with urllib.request.urlopen(req,timeout=1.2) as r: return r.status==200
    except Exception: return False

def plan(observation, history):
    system="You are the Planner agent for privacy redaction. Use native tool calls to select the next tool(s), based on observations and previous tool results. This is not a fixed pipeline: inspect observations, choose a useful next action, and call verify_output before stopping. You may stop only when evidence supports it. Never put document values, identifiers, names, addresses, or any PII in explanations or tool arguments. If enough evidence exists, call redact_text then verify_output. If findings are ambiguous, call validate_candidate."
    payload={"model":os.getenv("OLLAMA_MODEL",OLLAMA_MODEL),"stream":False,"messages":[{"role":"system","content":system},{"role":"user","content":json.dumps({"observations":observation,"previous_steps":history,"remaining_budget":8})}],"tools":[_tool_schema(n) for n in TOOLS],"options":{"temperature":0.1}}
    req=urllib.request.Request(_local_base_url()+"/api/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r: data=json.loads(r.read())
    message=data.get("message",{}); calls=message.get("tool_calls",[]) or []
    selected=[]
    for call in calls:
        name=call.get("function",{}).get("name")
        if name in TOOLS and name not in selected: selected.append(name)
    if not selected:
        try:
            content=json.loads(message.get("content","{}")); selected=[x for x in content.get("tools",[]) if x in TOOLS]
            return {"thought":str(content.get("thought","Planner selected next action"))[:180],"tools":selected,"stop":bool(content.get("stop",False))}
        except Exception: return {"thought":"Planner did not return a valid tool call; deterministic safeguards will take over","tools":[],"stop":True}
    return {"thought":"Planner selected tools using Ollama function calling","tools":selected,"stop":False}
