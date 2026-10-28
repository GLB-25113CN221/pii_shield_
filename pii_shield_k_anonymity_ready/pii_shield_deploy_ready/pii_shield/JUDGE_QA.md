# PII Shield Agent — exhibition Q&A cheat sheet

**Q: Why use an agent instead of a fixed rules pipeline?**  
The Planner asks the local LLM to select the next tool based on observations and prior steps. It can request detection, contextual validation, redaction, or verification, then stop or use remaining budget. Rules remain important for deterministic identifier checks. If Ollama is unavailable, the app explicitly reports rule-only mode rather than pretending an agent ran.

**Q: Is this fully autonomous?**  
No. It is a bounded local agent with an eight-step tool budget and deterministic safeguards. Ambiguous cases are queued for human review. LLM decisions can be wrong.

**Q: Does any document leave the computer?**  
The app itself calls only a localhost Ollama endpoint. OCR and rule-based detection run locally. Initial dependency/model downloads require network access. Verify your machine's network configuration before processing sensitive files.

**Q: How accurate is it?**  
There is no defensible universal accuracy number. The Evaluation tab reports precision, recall and F1 on a small, explicitly synthetic dataset. Those results are not a real-world benchmark and do not predict performance on unseen documents.

**Q: What does the checksum do?**  
It rejects many malformed Aadhaar/card candidates. A passing checksum is not proof of issuance or identity, and OCR errors can still cause misses.

**Q: What does it miss?**  
Potential misses include handwriting, QR/barcodes, embedded attachments, comments, tracked changes, unusual layouts, low-quality scans, unseen ID formats, contextual references, and rephrased/obfuscated PII.

**Q: Why can names and addresses be missed?**  
NER models are imperfect and language coverage varies. The app uses label heuristics and can use a multilingual NER model only when the compatible model is installed/cached locally. Without it, detection degrades gracefully.

**Q: Is this DPDP compliant?**  
No compliance claim is made. The system supports masking and auditability; legal and security compliance depends on deployment, procedures, and applicable obligations.

**Q: What is recorded in the audit database?**  
Document identifier, file type, language, PII categories/counts, verification status, and a heuristic risk indicator. Matched values are not intentionally written to audit records.

**Q: Why is scanned PDF output image-only?**  
The page is rasterized, OCR is used to locate sensitive word boxes, those boxes are masked, and the page is rebuilt. This makes text non-searchable and can reduce accessibility or document fidelity.


**Q: What is different about the improved detection stack?**  
It combines Presidio-compatible pattern recognizers and existing Indian identifier validators with AI4Bharat IndicNER for 11 supported Indian languages, then adds a transparent heuristic layer for quasi-identifier combinations and relationship signals. These components are not individually claimed as novel. The project contribution is the integrated, locally run workflow and a benchmark that measures per-category detection and residual leakage.

**Q: Does IndicNER work automatically?**  
The model is gated on Hugging Face. The user must accept its conditions and cache the model weights. By default the app does not download model weights while processing documents. Without the model, the app labels the NER status as unavailable and uses weaker fallback rules.

**Q: Is the privacy risk score a probability that someone can be re-identified?**  
No. It is an interpretable heuristic combining direct-identifier counts, quasi-identifier indicators, and nearby relation cues. It must not be interpreted as a calibrated probability or proof of safety.


**Q: Which research ideas are actually implemented?**  
The current code combines: (1) multilingual named-entity detection using AI4Bharat IndicNER when the gated model is available; (2) Presidio built-in recognizers plus custom Indian identifier patterns; (3) an interpretable heuristic for quasi-identifier combinations; (4) lightweight relationship-signal extraction between adjacent detected entities; and (5) the existing independent red-team verification/retry loop. The contextual risk and relationship components are heuristics, not a full trained relation-extraction or re-identification model. Risk-adaptive text generalization and active learning are future extensions, not claimed as implemented.


## What is new compared with Presidio?

We do not claim regex detection, NER, or anonymization is new; Presidio already supports those capabilities. Our prototype combines AI4Bharat IndicNER (when gated weights are available), India-specific identifier checks, quasi-identifier combination and relationship signals, uncertainty-prioritized human review, risk-adaptive action recommendations, and a bounded independent post-redaction verification loop. The contribution must be judged by a controlled comparison against a configured Presidio baseline on the same labelled test set. Current synthetic tests are smoke tests and do not establish real-world superiority.

## Does PII Shield calculate the real probability that a person can be re-identified?

No. It reports an interpretable heuristic risk indicator based on direct identifier categories, quasi-identifier cues, and relation patterns. It is not a calibrated probability or a guarantee of safety.
