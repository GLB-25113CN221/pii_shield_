"""Agentic processing with an LLM-selected tool loop and explicit rule-only fallback."""
import time, re
from collections import Counter
from config import MAX_VERIFY_ITERATIONS
from detectors.identifiers import detect_identifiers
from ner.multilingual import detect_ner
from redactors.text import redact_text
from audit.db import log_event
from reports.compliance_pdf import make_report
from agents.planner import ollama_available, plan
from agents.context_reviewer import review
from agents.red_team import inspect
from detectors.base import Finding
from detectors.contextual_risk import assess_privacy_risk
from detectors.privacy_policy import recommend_actions, prioritize_review
from detectors.presidio_pipeline import presidio_status
from ner.multilingual import ner_status

MAX_STEPS=8

def process_text(text: str, file_type="txt", language="Auto-detect", step_budget=MAX_STEPS):
    trace=[]; findings=[]; output=text; agent_mode=ollama_available(); remaining=max(1,min(int(step_budget),MAX_STEPS)); history=[]
    def record(kind, observation, tool=None):
        trace.append({"step":kind,"tool":tool or kind,"observation":str(observation)[:220],"reflection":""})
    if agent_mode:
        while remaining>0:
            try:
                decision=plan({"characters":len(text),"finding_count":len(findings),"findings_by_type":dict(Counter(f.pii_type for f in findings)),"output_redacted":output!=text},history)
                tools=decision.get("tools",[]); thought=decision.get("thought","Planner reflection"); stop=bool(decision.get("stop",False))
                record("Planner decision",{"tools":tools,"stop":stop,"reflection":thought},"planner")
            except Exception as exc:
                record("Planner unavailable; deterministic safeguards engaged",type(exc).__name__,"planner"); agent_mode=False; break
            if stop or not tools: break
            for tool in tools:
                if remaining<=0: break
                remaining-=1
                if tool=="detect_identifiers":
                    new=detect_identifiers(text); findings=_merge(findings,new); obs={"count":len(new),"types":sorted({f.pii_type for f in new})}
                elif tool=="detect_names_addresses":
                    new=detect_ner(text); findings=_merge(findings,new); obs={"count":len(new),"types":sorted({f.pii_type for f in new})}
                elif tool=="validate_candidate":
                    pending=[f for f in findings if f.status in ("pending","review")][:4]; results=[]
                    for f in pending:
                        try:
                            r=review(text,f); f.confidence=r["confidence"]; f.reason=r["reason"]
                            f.status="rejected" if r["decision"]=="reject" else ("high" if r["decision"]=="redact" and f.confidence>=.8 else "review")
                            results.append({"type":f.pii_type,"decision":r["decision"],"confidence":f.confidence,"reason":r["reason"]})
                        except Exception: f.status="review"
                    obs=results or {"pending":0}
                elif tool=="redact_text":
                    accepted=[f for f in findings if f.status!="rejected"]
                    output=redact_text(text,accepted); obs={"redactions":len(accepted)}
                elif tool=="verify_output":
                    ver=inspect(output,findings); obs={k:v for k,v in ver.items() if k!="findings"}
                    if not ver["verified"]:
                        residual=ver["findings"]
                        if residual: output=redact_text(output,residual)
                    else: stop=True
                elif tool in ("extract_text","ocr_page","rasterize_pdf","redact_image_boxes","redact_pdf","redact_docx"):
                    obs="Tool is available for format-specific document handler; current input is text."
                else: obs="No-op: unsupported for current text payload"
                record("Tool observation",obs,tool); history.append({"tool":tool,"observation":obs})
                if tool=="verify_output" and obs.get("verified",False): break
            if stop: break
    if not agent_mode:
        record("Run mode","Rule-only mode (no agent)","mode")
        findings=_merge(findings,detect_identifiers(text)); findings=_merge(findings,detect_ner(text))
        # Heuristic context review only; never imply an LLM decision.
        for f in findings:
            if f.status in ("pending","review"):
                f.status="review"; f.reason="Ambiguous candidate; rule-only mode cannot adjudicate context"
                f.confidence=min(f.confidence,.69)
        output=redact_text(text,[f for f in findings if f.status!="rejected"])
    # Always run independent deterministic red-team verification; bounded retries.
    verification=inspect(output,findings)
    tries=0
    while not verification["verified"] and tries<MAX_VERIFY_ITERATIONS:
        tries+=1; residual=verification.get("findings",[])
        if residual: output=redact_text(output,residual)
        else: break
        record("Red-team retry",{"attempt":tries,"residual_count":len(residual),"types":verification["residual_types"]},"red_team")
        verification=inspect(output,findings)
    record("Red-team verification",{k:v for k,v in verification.items() if k!="findings"},"red_team")
    counts=dict(Counter(f.pii_type for f in findings if f.status!="rejected"))
    active_findings=[f for f in findings if f.status!="rejected"]
    privacy_risk=assess_privacy_risk(text,active_findings)
    risk=privacy_risk["score"]
    policy_recommendations=recommend_actions(active_findings,privacy_risk,profile="balanced")
    prioritized_review=prioritize_review([f for f in findings if f.status=="review" or f.status=="pending"],privacy_risk)
    presidio_path=presidio_status()
    ner_info=ner_status()
    record("Detection stack",{"presidio":presidio_path,"ner_model":ner_info["model"],"ner_status":ner_info["status"]},"detection_stack")
    doc_id=log_event(file_type,language,findings,"VERIFIED" if verification["verified"] else "RESIDUAL_OR_UNCERTAIN",risk)
    report={"document_id":doc_id,"file_type":file_type,"language":language,"counts":counts,"mode":"Agent mode (local Ollama)" if agent_mode else "Rule-only mode (no agent)","verification_status":"VERIFIED" if verification["verified"] else "RESIDUAL_OR_UNCERTAIN","risk_score":risk,"risk_explanation":"Heuristic indicator combining detected categories and quasi-identifier signals; not a calibrated probability or security guarantee.","privacy_risk":privacy_risk,"policy_recommendations":policy_recommendations,"prioritized_review_queue":prioritized_review,"detection_stack":{"presidio":presidio_path,"ner":ner_info},"safeguards":["masking","local processing","PII-free audit log"],"trace":trace,"findings":[dict(f.public(),reason=getattr(f,"reason","Detector match"),detector=f.layer) for f in findings],"human_review_queue":[dict(f.public(),reason=getattr(f,"reason","Low confidence")) for f in findings if f.status=="review"]}
    report["pdf_report"]=make_report(report)
    return output,report

def _merge(a,b):
    seen={(f.pii_type,f.start,f.end) for f in a}
    return a+[f for f in b if (f.pii_type,f.start,f.end) not in seen]
