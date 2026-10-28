# PII Shield detection update

## Implemented in this build

1. **AI4Bharat IndicNER integration** (`ner/multilingual.py`): token-classification inference for the 11 model-card languages (Assamese, Bengali, Gujarati, Hindi, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, Telugu). Predictions are converted into the project's span-based `Finding` contract, retaining offsets into the original text. Model weights are loaded from the local cache by default. Downloads require explicit opt-in and Hugging Face access approval.
2. **Presidio recognition** (`detectors/presidio_pipeline.py`): custom `PatternRecognizer`s for Indian identifiers; selected built-in Presidio recognizers for email, phone, credit card, IP and URL when the AnalyzerEngine path is available; fallback to custom PatternRecognizers/patterns when the spaCy model or AnalyzerEngine is unavailable. Existing project validators remain in place.
3. **Contextual privacy-risk indicators** (`detectors/contextual_risk.py`): counts age, occupation, specific-location, date/event and relationship cues. Nearby detected entities and relationship phrases produce category-only relation signals. The report contains categories/counts, not the actual matched values.
4. **Post-detection report/UI integration**: processing reports show the detection stack status and contextual-risk signals; the existing red-team verifier and bounded retry loop remain in place.
5. **Synthetic coverage**: the evaluation examples and tests now include explicit field labels in the 11 IndicNER language scripts.

## Deliberate limits

- The contextual-risk score is a transparent heuristic, not a calibrated probability of re-identification.
- Relationship extraction is a small rule-based signal extractor, not a trained relation-extraction model or a complete knowledge graph.
- This build does not implement active-learning model retraining or automatic utility-preserving text generalization. These remain possible future extensions.
- IndicNER is gated on Hugging Face. The model must be accepted/downloaded by the user. This build environment did not have the gated weights, so real model inference has not been claimed as tested.
- The full Presidio AnalyzerEngine path requires `presidio-analyzer` and `en_core_web_sm`. This build environment did not have those dependencies, so its fallback and graceful degradation are tested, not the full AnalyzerEngine path.

## Setup for IndicNER

1. Accept the model conditions at https://huggingface.co/ai4bharat/IndicNER.
2. Authenticate with Hugging Face using `hf auth login` or set `HF_TOKEN` securely.
3. Set `PII_NER_ALLOW_DOWNLOAD=true` before starting the app for the first model download. The weights are about 667 MB. Set it back to `false` for offline runs.
4. The application processes document content locally; only model files/configuration are fetched during an explicitly enabled download.

## References

- AI4Bharat IndicNER / Naamapadam: https://huggingface.co/ai4bharat/IndicNER and https://arxiv.org/abs/2212.10168
- Microsoft Presidio Analyzer: https://microsoft.github.io/presidio/analyzer/
- READI relation-aware de-identification: https://pmc.ncbi.nlm.nih.gov/articles/PMC11141830/
- LeakageBench document-level leakage evaluation: https://aclanthology.org/2026.findings-emnlp.2350/
- Truthful text sanitization guided by inference attacks: https://www.sciencedirect.com/science/article/pii/S1568494625013262
- Neural text sanitization with privacy risk indicators: https://link.springer.com/article/10.1007/s10579-026-09911-1

## Additional research-inspired identification components in this update

6. **Quasi-identifier combination analysis** (`detectors/contextual_risk.py`): expanded multilingual cues for age, occupation, location specificity, date/event, and relationship terms. The report exposes category counts and transparent score components. It is a heuristic signal, not a probability of re-identification.
7. **Relationship-aware signals** (`detectors/contextual_risk.py`): bounded-window relation patterns connect nearby detected entity categories (e.g., person→organization via employment wording). Reports contain relation labels and entity categories only, not entity values. This is a lightweight rule-based approximation, not a trained relation extraction model or knowledge graph.
8. **Risk-adaptive action recommendations** (`detectors/privacy_policy.py`): recommends `redact`, `redact_or_generalize`, `generalize_or_review`, or `human_review` under a strict, balanced, or utility-preserving policy. In this build, recommendations are advisory; they do not silently generalize or alter the existing redaction output.
9. **Uncertainty-prioritized review** (`detectors/privacy_policy.py`): ranks pending/low-confidence findings using uncertainty, direct-identifier impact, and document risk. This is active-learning-inspired review prioritization, not automated model training.
10. **Mutation robustness smoke test** (`evaluation.py`, Evaluation tab): tests synthetic variations including whitespace/hyphens in phone numbers, Devanagari digits, missing labels, and negative examples. It reports per-case pass/fail; this small suite is not a real-world benchmark.
11. **Independent post-redaction verification**: the existing verifier/red-team loop re-runs the available detectors on the output and attempts bounded repairs. This cannot prove the document contains no PII, especially if the leak is semantic, hidden in an unsupported object, or missed by all detectors.

### Suggested research framing

The research-inspired contribution is the integration and evaluation of multilingual identifier/NER detection, quasi-identifier combination signals, relationship-aware review, risk-adaptive recommendations, and post-redaction leakage checks. These are adaptations of established ideas, not a claim that each technique is new or that this prototype reproduces the referenced papers in full.
