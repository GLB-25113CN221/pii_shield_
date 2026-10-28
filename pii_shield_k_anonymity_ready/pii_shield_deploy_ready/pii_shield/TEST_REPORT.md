# Verification report — detection update

Executed in the build environment on 2026-10-27:

- `python -m compileall -q .` — passed.
- `pytest -q` — **45 passed, 1 skipped**. The skipped test is environment-dependent Streamlit AppTest.
- `evaluation.evaluate('rule-only')` — ran over **23 synthetic examples**, including field-label examples from the 11 IndicNER language scripts. This is a smoke-test dataset, not a real-world benchmark.
- `python evaluate.py` — the separate built-in synthetic email evaluation ran successfully over 120 samples.
- A text-processing smoke test confirmed identifier/name detection, a contextual-risk report, detector-stack status, and redaction output.

**Not verified in this environment:** live IndicNER inference because the model is gated and weights were not cached; full Presidio AnalyzerEngine because `presidio-analyzer`/`en_core_web_sm` were not installed in this build runtime; live Ollama agent run; Streamlit AppTest; and Tesseract OCR quality on representative documents. The code includes graceful fallbacks, but these integrations should be tested in the target environment after setup.

No claim of improved real-world precision/recall is made until a labelled held-out dataset is evaluated.

- Added unit tests for space/hyphen/Devanagari mobile detection, privacy-policy recommendations, value-free review prioritization, risk-score components, and mutation-suite coverage.
- `evaluation.evaluate_robustness()` — **10/10 synthetic mutation smoke cases passed** in this runtime after the phone-number normalization update. This is a small synthetic smoke test, not a benchmark; model-dependent NER results can differ when IndicNER weights are installed.
- New risk-policy and review-priority output is advisory and does not change the actual redaction strategy.


## Tabular k-anonymity feature verification — 2026-10-28

- `python -m compileall -q .` — passed after adding the CSV k-anonymity tab and transformation module.
- `pytest -q` — **53 passed, 1 skipped** in this build environment, including eight new tests for k validation, direct-identifier removal, generalization, missing values, and post-transformation equivalence-class verification.
- The synthetic CSV demo in `demo_assets/k_anonymity_sample.csv` was transformed at `k=3`; the generated report verified a minimum equivalence-class size of 4 after generalization.

These tests establish behaviour for the included test cases only. They are not a formal privacy proof, a real-world re-identification study, or certification that an arbitrary dataset is safe to publish. The feature is conditional on the selected quasi-identifiers and does not guarantee l-diversity or t-closeness.
