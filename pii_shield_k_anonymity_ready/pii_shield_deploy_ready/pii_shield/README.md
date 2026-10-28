---
title: PII Shield India
emoji: 🛡️
colorFrom: indigo
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# PII Shield Agent

Local-first, multilingual PII masking prototype for Indian documents. Streamlit UI; local Ollama planner/reviewer; regex/checksum detectors; optional cached multilingual NER; OCR; PDF/DOCX/image redaction; synthetic evaluation; value-free SQLite audit metadata.

## Requirements
- Python 3.10+
- Tesseract OCR with `eng` and `hin` language data for scanned documents/images
- Ollama and a locally pulled model for agent mode (default `qwen2.5:7b`)
- Optional but recommended: AI4Bharat IndicNER for Assamese, Bengali, Gujarati, Hindi, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, and Telugu. The Hugging Face model is gated: accept its conditions and authenticate before downloading. By default PII Shield only loads locally cached weights.
- Optional: `presidio-analyzer` custom PatternRecognizers provide a Presidio-compatible recognition pipeline for Indian identifiers; AnalyzerEngine is used when `en_core_web_sm` is installed, otherwise the app uses its PatternRecognizer fallback plus existing validators.

## Windows setup
1. Install Python 3.10+ and Tesseract. Ensure `tesseract.exe` is on PATH; install English and Hindi language data.
2. Install Ollama from its official installer, then run `ollama pull qwen2.5:7b` in PowerShell.
3. Open PowerShell in this folder and run:
   ```powershell
   py -3.10 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. (Optional, for Presidio AnalyzerEngine context enhancement) install its small English spaCy model:
   ```powershell
   python -m spacy download en_core_web_sm
   ```
   Without it, custom Presidio PatternRecognizers still run through the documented fallback.
5. Start the app with `streamlit run app.py`.

## macOS setup
1. Install Python 3.10+, then `brew install tesseract tesseract-lang` (package availability may vary by Homebrew version).
2. Install Ollama and run `ollama pull qwen2.5:7b`.
3. In Terminal, from this folder:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Configuration
- `OLLAMA_URL` defaults to `http://127.0.0.1:11434`
- `OLLAMA_MODEL` defaults to `qwen2.5:7b`
- `PII_NER_MODEL` defaults to `ai4bharat/IndicNER`. The model must be accepted on Hugging Face and cached locally for offline use. After accepting the model conditions, authenticate using `hf auth login` (or set `HF_TOKEN`), then set `PII_NER_ALLOW_DOWNLOAD=true` for the first download. Set it back to `false` for offline runs.
- `PII_NER_ALLOW_DOWNLOAD` defaults to `false`; document text is processed locally and is not sent to Hugging Face. Only model weights/configuration are downloaded when you explicitly enable downloads. The model weights are about 667 MB according to the Hugging Face file listing; allow extra disk space for PyTorch and the cache. To enable the first download, first accept the model conditions at https://huggingface.co/ai4bharat/IndicNER and authenticate with Hugging Face. Then set `PII_NER_ALLOW_DOWNLOAD=true` before starting Streamlit. In Colab, set `os.environ["HF_TOKEN"]` from a Colab secret and `os.environ["PII_NER_ALLOW_DOWNLOAD"]="true"` before launching the app; do not paste a token into a shared notebook.
- Privacy-risk analysis reports heuristic counts of quasi-identifiers and nearby relationship signals. It is not a calibrated re-identification probability.
- `MAX_FILE_MB` defaults to 20.
- If Ollama cannot be reached, the app uses and labels **Rule-only mode (no agent)**. It does not simulate an agent.

## Run and test
```bash
streamlit run app.py
python demo_assets/generate.py
pytest -q
```
The app's Evaluation tab reports metrics on a small synthetic dataset and can run a deterministic mutation-robustness smoke test. Neither is a real-world benchmark. The detection stack combines format/checksum validators, selected built-in Presidio recognizers plus custom Indian PatternRecognizers, AI4Bharat IndicNER when available, multilingual field-label rules, quasi-identifier combination signals, relationship-aware heuristics, risk-adaptive action recommendations, uncertainty-prioritized review, and an independent bounded post-redaction verification loop. The Evaluation tab also contains a small mutation-robustness smoke test. These are research-inspired integrations, not a reproduction of the cited papers or a claim of measured real-world superiority. IndicNER model card: https://huggingface.co/ai4bharat/IndicNER. Presidio Analyzer documentation: https://microsoft.github.io/presidio/analyzer/. Audit logs store category/count metadata, not matched values. See `DETECTION_DESIGN.md` for exactly what was implemented, `LIMITATIONS.md` for caveats, and `JUDGE_QA.md` before presenting.

## Tabular k-anonymity feature

The **K-Anonymity** tab accepts a structured CSV table. Select direct-identifier columns to remove, select quasi-identifier (QI) columns to generalize, and choose a target `k` (at least 2). The app applies global generalization to the selected QIs and verifies that every equivalence class in the output has at least `k` rows. It downloads both the transformed CSV and a verification report.

Important scope limits:
- This is a table-level release transformation; it does not make arbitrary text, PDF, DOCX, or image documents k-anonymous.
- The guarantee applies only to the selected QI columns and the released table as processed. Unselected columns, metadata, outside datasets, or later joins can create additional risks.
- Direct identifiers must be selected for removal; check the output before release.
- k-anonymity does not prevent sensitive-attribute disclosure. Consider l-diversity/t-closeness, threat modelling, small-cell suppression, and human review for sensitive datasets.
- Generalization may reduce data utility. Test several k values and inspect the output before using it.
- This implementation is a demonstrator, not a formal privacy certification or a guarantee against every re-identification attack.

See `K_ANONYMITY.md` for the method and validation caveats.

## Tool architecture
Planner-selected tools: `extract_text`, `ocr_page`, `rasterize_pdf`, `detect_identifiers`, `detect_names_addresses`, `validate_candidate`, `redact_text`, `redact_image_boxes` (image redaction utility), `redact_pdf`, `redact_docx`, and `verify_output`. The LLM chooses from available tool names based on observations, within an eight-step budget. Format-specific PDF/image/DOCX handlers invoke their respective redaction utilities. A deterministic red-team pass retries boundedly.

This project supports masking and auditability. It does not certify legal compliance or guarantee complete PII removal.
