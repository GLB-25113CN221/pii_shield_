"""PII Shield India Streamlit demo. See README for scope and limitations."""
import io, json, zipfile, re
from pathlib import Path
import streamlit as st
from PIL import Image
from agents.router import route
from agents.orchestrator import process_text
from detectors.identifiers import detect_identifiers
from ner.multilingual import detect_ner
from ocr.engine import ocr_image
from redactors.image import redact_image
from redactors.pdf import redact_pdf, pdf_text
from redactors.docx import redact_docx, docx_text
from audit.db import rows
from demo_assets.generate import generate
from config import MAX_FILE_MB, SUPPORTED_LANGUAGES
from evaluation import evaluate
from agents.planner import ollama_available
from tools import redact_scanned_pdf
from ui_theme import apply_theme, intro, AGENT_LOOP

st.set_page_config(page_title="PII Shield India",page_icon="🛡️",layout="wide")
apply_theme()
st.warning("Privacy notice: process only files you are authorized to use. Files may contain sensitive data. This prototype is not a legal compliance certification.")
consent=st.checkbox("I understand and consent to process this content locally for sanitization.",key="consent")
lang=st.sidebar.selectbox("Detection language",SUPPORTED_LANGUAGES)
ui_lang=st.sidebar.radio("UI language",["English","हिन्दी"],horizontal=True)
st.sidebar.markdown("### How the agent works")
st.sidebar.markdown(AGENT_LOOP,unsafe_allow_html=True)
st.sidebar.caption("LLM availability is checked locally. No agent behaviour is simulated when Ollama is unavailable.")
st.sidebar.caption("DPDP: Section 8(5) addresses reasonable security safeguards. Penalties depend on the applicable Schedule and facts; consult counsel.")
tabs=st.tabs(["Text","Image","Document","Batch","Dashboard","Audit Log","Evaluation","K-Anonymity"])
AUDIT_COLUMNS=["timestamp","document_id","file_type","language","types","counts","verification","risk"]
detect_all=lambda t:detect_identifiers(t)+detect_ner(t)

def trace_view(report):
    with st.expander("Live Agent Trace",expanded=True):
        st.caption(report.get("mode","Mode not reported"))
        for i,t in enumerate(report.get("trace",[]),1):
            st.write(f"{i}. **{t.get('step','Step')}** · tool: `{t.get('tool','—')}`")
            st.caption(str(t.get("observation", ""))[:220])
            if t.get("reflection"): st.caption("Reflection: "+str(t["reflection"]))
    queue=report.get("human_review_queue",[])
    if queue:
        with st.expander(f"Human review queue ({len(queue)})",expanded=True):
            st.warning("Low-confidence items are highlighted for human approval. Review the source document before relying on the output.")
            for item in queue: st.write(f"• {item.get('type')} — confidence {item.get('confidence',0):.2f} — {item.get('reason','Needs review')}")

def downloads(output,name,report,key):
    """Download buttons. `key` keeps widget IDs unique across tabs."""
    st.download_button("Download sanitized file",output,file_name=name,key=f"{key}_file")
    clean={k:v for k,v in report.items() if k!="pdf_report"}
    st.download_button("Download JSON report",json.dumps(clean,ensure_ascii=False,indent=2),file_name="compliance_report.json",mime="application/json",key=f"{key}_json")
    st.download_button("Download PDF report",report["pdf_report"],file_name="dpdp_compliance_report.pdf",mime="application/pdf",key=f"{key}_pdf")

def run_safely(fn):
    """Run fn(); show a readable error in the page instead of a Streamlit traceback."""
    try: return fn()
    except Exception as exc:
        st.error(f"{type(exc).__name__}: {exc}"); return None

# Results are kept in st.session_state. Clicking a download button re-runs the script, and
# without this the sanitized output would disappear the moment you click "Download".
def show_text_result(r):
    a,b=st.columns(2)
    a.text_area("Before",r["before"],height=180,disabled=True,key="t_before"); b.text_area("After",r["after"],height=180,disabled=True,key="t_after")
    st.metric("Privacy risk indicator",f"{r['rep']['risk_score']}/100"); st.write(r["rep"]["risk_explanation"])
    risk_info=r["rep"].get("privacy_risk",{})
    if risk_info:
        with st.expander("Contextual / re-identification risk signals"):
            st.write("Risk band:",risk_info.get("level","unknown"))
            st.write("Quasi-identifier counts:",risk_info.get("quasi_identifier_indicator_counts",{}))
            st.write("Relationship signals:",len(risk_info.get("relationship_signals",[])))
            st.caption(risk_info.get("recommendation","Review the document context."))
            st.write("Score components:",risk_info.get("score_components",{}))
    policy=r["rep"].get("policy_recommendations",[])
    if policy:
        with st.expander("Risk-adaptive action recommendations"):
            st.caption("Recommendations only: the existing redaction pipeline remains responsible for actual masking.")
            st.dataframe([{k:item.get(k) for k in ("type","confidence","action","reason")} for item in policy],use_container_width=True)
    review_items=r["rep"].get("prioritized_review_queue",[])
    if review_items:
        with st.expander("Uncertainty-prioritized review (active-learning-inspired)"):
            st.caption("Highest uncertainty / privacy-impact items appear first. This prioritizes human review; it does not automatically train the model.")
            st.dataframe([{k:item.get(k) for k in ("type","confidence","priority","selection_reason")} for item in review_items],use_container_width=True)
    stack=r["rep"].get("detection_stack",{})
    if stack:
        st.caption("Presidio: "+str(stack.get("presidio","not reported")))
        st.caption("NER: "+str(stack.get("ner",{}).get("status","not reported")))
    trace_view(r["rep"])
    downloads(r["after"].encode("utf-8"),"sanitized.txt",r["rep"],"t")

def show_image_result(r):
    a,b=st.columns(2); a.image(r["before"],caption="Before"); b.image(r["after"],caption="After")
    trace_view(r["rep"]); downloads(r["png"],"sanitized.png",r["rep"],"i")

def show_doc_result(r):
    st.write("Router:",r["kind"],"→",r["tool"])
    if r.get("note"): st.info(r["note"])
    trace_view(r["rep"]); downloads(r["out"],r["name"],r["rep"],"d")

with tabs[0]:
    intro("Paste any text. Private details are replaced and you can compare before and after.")
    value=st.text_area("Paste text to sanitize",height=220,placeholder="नाम: राजेश कुमार\nEmail: demo.user@example.com")
    if st.button("Sanitize text",disabled=not consent):
        res=run_safely(lambda:process_text(value,"txt",lang))
        if res: st.session_state.res_text={"before":value,"after":res[0],"rep":res[1]}
    if "res_text" in st.session_state: show_text_result(st.session_state.res_text)

with tabs[1]:
    intro("Upload a photo or scan. Private details found by OCR are blacked out in the image.")
    upload=st.file_uploader("Upload JPG/PNG image",type=["jpg","jpeg","png","webp"],key="img")
    override=st.text_input("Tesseract OCR language override","eng+hin")
    if upload and st.button("Sanitize image",disabled=not consent):
        def do_image():
            if upload.size>MAX_FILE_MB*1024*1024: st.error("File exceeds configured size limit."); return None
            image=Image.open(upload); image.load()
            try: text,words=ocr_image(image,override)
            except Exception as exc:
                st.error(f"OCR failed: {exc}. Install Tesseract and the language packs in the override box (e.g. 'eng' only if Hindi is missing).")
                return None
            fs=detect_all(text)
            # Map character spans to OCR word boxes conservatively; redact all words overlapping a finding.
            boxes=[]; cursor=0
            for w in words:
                start=text.find(w["text"],cursor); end=start+len(w["text"]) if start>=0 else -1
                if start>=0 and any(f.start<end and f.end>start for f in fs):
                    x0,y0,x1,y1=w["box"]; boxes.append((x0-2,y0-2,x1+2,y1+2))
                if start>=0: cursor=end
            cleanimg=redact_image(image,boxes)
            buf=io.BytesIO(); cleanimg.save(buf,format="PNG")
            _,rep=process_text(text,"image",lang)
            return {"before":image.copy(),"after":cleanimg,"png":buf.getvalue(),"rep":rep}
        res=run_safely(do_image)
        if res: st.session_state.res_image=res
    if "res_image" in st.session_state: show_image_result(st.session_state.res_image)

with tabs[2]:
    intro("Upload a PDF, Word file, text file or CSV. You get back a cleaned copy and a compliance report.")
    upload=st.file_uploader("Upload PDF, DOCX, TXT or CSV",type=["pdf","docx","txt","csv"],key="doc")
    if upload and st.button("Sanitize document",disabled=not consent):
        def do_doc():
            data=upload.getvalue()
            if len(data)>MAX_FILE_MB*1024*1024: st.error("File exceeds configured size limit."); return None
            info=route(upload.name,data); ext=Path(upload.name).suffix.lower(); note=None
            if ext==".pdf":
                text=pdf_text(data)
                if not text.strip():
                    note="Scanned PDF detected. Pages are rasterized, preprocessed, OCR-scanned and rebuilt as image-only PDF."
                    out=redact_scanned_pdf(data,detect_all,override if 'override' in globals() else 'eng+hin')
                    _,rep=process_text("Scanned PDF: OCR redaction performed; text layer unavailable.","pdf",lang)
                else:
                    _,rep=process_text(text,"pdf",lang)
                    out=redact_pdf(data,detect_all)
                name="sanitized.pdf"
            elif ext==".docx":
                _,rep=process_text(docx_text(data),"docx",lang)
                out=redact_docx(data,detect_all); name="sanitized.docx"
            else:
                text=data.decode("utf-8-sig",errors="replace")
                clean,rep=process_text(text,ext[1:],lang); out=clean.encode("utf-8"); name="sanitized"+ext
            return {"kind":info["kind"],"tool":info["tool"],"rep":rep,"out":out,"name":name,"note":note}
        res=run_safely(do_doc)
        if res: st.session_state.res_doc=res
    if "res_doc" in st.session_state: show_doc_result(st.session_state.res_doc)

with tabs[3]:
    intro("Clean many files at once and download them together as one ZIP.")
    files=st.file_uploader("Upload multiple files",accept_multiple_files=True,type=["txt","csv","docx","pdf"],key="batch")
    if st.button("Sanitize batch",disabled=not (consent and files)):
        buf=io.BytesIO(); failed=[]
        with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as z:
            for f in files:
                data=f.getvalue(); ext=Path(f.name).suffix.lower()
                if len(data)>MAX_FILE_MB*1024*1024: failed.append(f"{f.name} (too large)"); continue
                try:
                    if ext in (".txt",".csv"):
                        clean,_=process_text(data.decode("utf-8-sig",errors="replace"),ext[1:],lang); z.writestr("sanitized_"+f.name,clean)
                    elif ext==".docx": z.writestr("sanitized_"+f.name,redact_docx(data,detect_all))
                    elif ext==".pdf": z.writestr("sanitized_"+f.name,redact_pdf(data,detect_all))
                except Exception as exc: failed.append(f"{f.name} ({type(exc).__name__})")
        st.session_state.res_batch={"zip":buf.getvalue(),"failed":failed}
    if "res_batch" in st.session_state:
        for item in st.session_state.res_batch["failed"]: st.warning(f"Skipped: {item}")
        st.download_button("Download batch ZIP",st.session_state.res_batch["zip"],"sanitized_batch.zip",mime="application/zip",key="b_zip")

with tabs[4]:
    intro("A summary of every document cleaned so far.")
    data=rows()
    st.metric("Documents audited",len(data))
    if data:
        import pandas as pd
        df=pd.DataFrame(data,columns=AUDIT_COLUMNS)
        st.metric("Average risk score",round(df["risk"].mean(),1)); st.dataframe(df[["file_type","language","verification","risk"]])
    if st.button("Generate synthetic demo files"):
        run_safely(lambda:st.write(generate()))
    if st.button("Live Demo — run sample text",disabled=not consent):
        res=run_safely(lambda:process_text("नाम: राजेश कुमार\nEmail: demo.user@example.com\nPAN: ABCPE1234F","txt",lang))
        if res: st.code(res[0]); trace_view(res[1])
with tabs[5]:
    st.subheader("PII-free audit log")
    import pandas as pd
    st.dataframe(pd.DataFrame(rows(),columns=AUDIT_COLUMNS))
    st.caption("Audit records contain categories/counts only, not matched values.")
st.markdown("---")
st.markdown('<div class="ps-foot"><b>Why this matters:</b> the DPDP Act provides for significant penalties, including up to ₹250 crore for specified failures under the Act\'s Schedule. This demo supports masking and auditability but does not certify compliance.</div>',unsafe_allow_html=True)

with tabs[6]:
    st.subheader("Synthetic evaluation")
    st.warning("This is a small synthetic dataset, not a real-world benchmark. Metrics depend on the hand-authored examples and optional locally cached NER model.")
    eval_mode=st.radio("Evaluation mode",["rule-only","agent"],horizontal=True)
    if eval_mode=="agent" and not ollama_available(): st.info("Ollama is unavailable. Agent-mode evaluation cannot run; start Ollama and load the configured model. No agent metrics are fabricated.")
    if st.button("Run evaluation"):
        try:
            result=evaluate(eval_mode)
            st.write("Mode:", "Agent mode (local Ollama)" if result["mode"]=="agent" and result["agent_available"] else "Rule-only mode (no agent)")
            st.write("Synthetic samples:",result["synthetic_samples"])
            import pandas as pd
            st.dataframe(pd.DataFrame.from_dict(result["metrics"],orient="index"),use_container_width=True)
        except Exception as exc: st.error(f"Evaluation could not complete: {type(exc).__name__}: {exc}")
    if st.button("Run mutation robustness smoke test"):
        try:
            from evaluation import evaluate_robustness
            robustness=evaluate_robustness()
            st.metric("Synthetic mutation pass rate",f"{robustness['passed']}/{robustness['total']} ({robustness['pass_rate']:.0%})")
            st.caption(robustness["warning"])
            import pandas as pd
            st.dataframe(pd.DataFrame(robustness["results"]),use_container_width=True)
        except Exception as exc: st.error(f"Robustness test could not complete: {type(exc).__name__}: {exc}")


with tabs[7]:
    import pandas as pd
    st.subheader("Tabular k-anonymity")
    st.write(
        "Create a release-oriented CSV by removing selected direct identifiers and generalizing "
        "selected quasi-identifiers until each retained quasi-identifier combination occurs in at least k rows."
    )
    st.warning(
        "This feature applies to structured CSV tables, not arbitrary free text, images, PDFs, or DOCX. "
        "It verifies k-anonymity only for the quasi-identifier columns you select. It does not guarantee "
        "l-diversity, t-closeness, differential privacy, or complete anonymity."
    )
    k_upload = st.file_uploader("Upload a CSV dataset", type=["csv"], key="kanon_csv")
    if k_upload:
        try:
            if k_upload.size > MAX_FILE_MB * 1024 * 1024:
                st.error(f"File exceeds configured size limit ({MAX_FILE_MB} MB).")
            else:
                upload_signature = str(hash(k_upload.getvalue()))
                if st.session_state.get("kanon_upload_signature") != upload_signature:
                    st.session_state.pop("kanon_result", None)
                    st.session_state["kanon_upload_signature"] = upload_signature
                k_df = pd.read_csv(io.BytesIO(k_upload.getvalue()))
                st.caption(f"Dataset preview: {len(k_df)} rows × {len(k_df.columns)} columns")
                st.dataframe(k_df.head(10), use_container_width=True)
                col_names = list(k_df.columns)
                def _looks_direct_id(name):
                    normalized = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
                    tokens = set(normalized.split("_"))
                    return bool(tokens & {"name", "phone", "mobile", "email", "aadhaar", "aadhar", "pan", "passport", "voter", "account", "customerid", "studentid"}) or normalized in {"id", "person_id", "user_id", "customer_id", "student_id", "full_name"}
                direct_defaults = [c for c in col_names if _looks_direct_id(c)]
                direct_cols = st.multiselect(
                    "Columns to remove completely (direct identifiers)",
                    options=col_names,
                    default=direct_defaults,
                    key="kanon_direct",
                    help="Remove names, phone numbers, emails, account numbers, IDs and any other direct identifiers before release."
                )
                qi_suggestions = [c for c in col_names if re.search(r"age|birth|date|gender|sex|district|city|state|location|ward|village|zip|pin|occupation|job|school|year", str(c), re.I) and c not in direct_cols]
                qi_cols = st.multiselect(
                    "Quasi-identifier columns",
                    options=[c for c in col_names if c not in direct_cols],
                    default=qi_suggestions,
                    key="kanon_qi",
                    help="Choose columns that could identify someone in combination, such as age, location, occupation or dates."
                )
                remaining_cols = [c for c in col_names if c not in direct_cols]
                extra_drop = st.multiselect(
                    "Other columns to exclude from the released dataset (optional)",
                    options=[c for c in remaining_cols if c not in qi_cols],
                    default=[],
                    key="kanon_extra_drop",
                    help="Use this to remove sensitive attributes or columns that the recipient does not need."
                )
                k_value = st.number_input("Target k value", min_value=2, max_value=max(2, len(k_df)), value=min(3, max(2, len(k_df))), step=1, key="kanon_k")
                st.caption("Example: k = 3 means every combination of the selected quasi-identifiers must be shared by at least three rows.")
                if st.button("Generalize and verify k-anonymity", key="kanon_run", disabled=not consent):
                    try:
                        if not qi_cols:
                            st.error("Select at least one quasi-identifier column.")
                        else:
                            from privacy.k_anonymity import anonymize_dataframe
                            working_df = k_df.drop(columns=extra_drop).copy()
                            anon_df, kanon_report = anonymize_dataframe(
                                working_df,
                                quasi_identifier_columns=qi_cols,
                                k=int(k_value),
                                direct_identifier_columns=direct_cols,
                            )
                            kanon_report["additional_columns_dropped"] = extra_drop
                            st.session_state.kanon_result = {
                                "csv": anon_df.to_csv(index=False).encode("utf-8-sig"),
                                "preview": anon_df.head(25),
                                "report": kanon_report,
                            }
                    except Exception as exc:
                        st.error(f"k-anonymity processing failed: {type(exc).__name__}: {exc}")
                if "kanon_result" in st.session_state:
                    result = st.session_state.kanon_result
                    rep = result["report"]
                    st.divider()
                    if rep.get("verified_k_anonymity"):
                        st.success(f"Verified for selected quasi-identifiers: every equivalence class has at least k={rep['k']} rows.")
                    else:
                        st.error("The output did not pass the k-anonymity verification.")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Rows retained", rep["output_rows"])
                    m2.metric("Equivalence classes", rep["equivalence_classes"])
                    m3.metric("Smallest class", rep["minimum_equivalence_class_size"])
                    st.write("Generalization levels:", rep["generalization_levels"])
                    st.write("Generalized columns:", rep["quasi_identifier_columns"])
                    st.dataframe(result["preview"], use_container_width=True)
                    st.download_button("Download k-anonymized CSV", result["csv"], file_name="k_anonymized_dataset.csv", mime="text/csv", key="kanon_download_csv")
                    st.download_button("Download verification report (JSON)", json.dumps(rep, ensure_ascii=False, indent=2), file_name="k_anonymity_report.json", mime="application/json", key="kanon_download_report")
                    st.info(rep["warning"])
        except Exception as exc:
            st.error(f"Could not read CSV: {type(exc).__name__}: {exc}")
