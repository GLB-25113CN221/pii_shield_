from detectors.identifiers import detect_identifiers
from ner.multilingual import detect_ner
def types(text): return {x.pii_type for x in detect_identifiers(text)}
def test_pan_valid(): assert "PAN" in types("ABCPE1234F")
def test_pan_invalid_fourth_char(): assert "PAN" not in types("ABCXE1234F")
def test_email(): assert "EMAIL" in types("demo.user@example.com")
def test_mobile(): assert "MOBILE" in types("9876543210")
def test_ifsc(): assert "IFSC" in types("HDFC0001234")
def test_gstin(): assert "GSTIN" in types("27ABCPE1234F1Z5")
def test_passport(): assert "PASSPORT" in types("A1234567")
def test_vehicle(): assert "VEHICLE_PLATE" in types("DL3CAB1234")
def test_voter(): assert "VOTER_ID" in types("ABC1234567")
def test_upi(): assert "UPI_ID" in types("person@bank")
def test_pin(): assert "PIN_CODE" in types("201001")
def test_bank_account_review(): assert "BANK_ACCOUNT" in types("Account No: 123456789012")
def test_hindi_label(): assert any(f.pii_type=="PERSON" for f in detect_ner("नाम: राजेश कुमार"))
def test_marathi_label(): assert any(f.pii_type=="PERSON" for f in detect_ner("नाव: प्रिया शर्मा"))
def test_tamil_label(): assert any(f.pii_type=="PERSON" for f in detect_ner("பெயர்: குமார்"))

def test_contextual_risk_detects_quasi_identifier_combination():
    from detectors.contextual_risk import assess_privacy_risk
    result = assess_privacy_risk("A 42-year-old teacher lives in a village in Sector 12 and received an award.", [])
    assert result["level"] == "high"
    assert result["combination_warning"] is True
    assert result["quasi_identifier_indicator_counts"]["age"] >= 1


def test_relationship_signals_do_not_include_entity_values():
    from detectors.contextual_risk import assess_privacy_risk
    from detectors.base import Finding
    text = "Ramesh works at ABC Hospital"
    findings = [Finding("PERSON", 0, 6, .9, "Ramesh"), Finding("ORGANIZATION", 16, 29, .8, "ABC Hospital")]
    result = assess_privacy_risk(text, findings)
    assert result["relationship_signals"]
    assert "Ramesh" not in str(result["relationship_signals"])
    assert "ABC Hospital" not in str(result["relationship_signals"])


def test_presidio_optional_pipeline_is_graceful():
    from detectors.presidio_pipeline import detect_with_presidio
    findings, path = detect_with_presidio("PAN ABCPE1234F")
    assert isinstance(findings, list)
    assert isinstance(path, str)


def test_ner_status_reports_indicner_configuration():
    from ner.multilingual import ner_status
    status = ner_status()
    assert status["model"] == "ai4bharat/IndicNER"
    assert status["status"]


def test_indicner_results_keep_original_text_offsets(monkeypatch):
    import ner.multilingual as multilingual
    monkeypatch.setattr(multilingual, "_get_indicner", lambda: (lambda line: [
        {"entity_group": "PER", "start": 0, "end": 5, "score": 0.93}
    ]))
    monkeypatch.setattr(multilingual, "_load_spacy", lambda: None)
    text = "રમેશ test\nதமிழ் line"
    found = multilingual.detect_ner(text)
    model_findings = [f for f in found if f.layer == "ai4bharat_indicner"]
    assert model_findings
    item = model_findings[0]
    assert text[item.start:item.end] == item.value
    assert item.pii_type == "PERSON"


def test_indicner_maps_location_and_organization_labels():
    from ner.multilingual import _kind_from_label
    assert _kind_from_label("LOC") == "LOCATION"
    assert _kind_from_label("ORG") == "ORGANIZATION"
    assert _kind_from_label("PER") == "PERSON"


def test_field_label_fallback_covers_all_indicner_scripts():
    from ner.multilingual import detect_ner
    examples = [
        ("নাম: ৰাহুল দাস", "ৰাহুল দাস"),
        ("নাম: অনন্যা সেন", "অনন্যা সেন"),
        ("નામ: આરવ પટેલ", "આરવ પટેલ"),
        ("नाम: राजेश कुमार", "राजेश कुमार"),
        ("ಹೆಸರು: ಕಾವ್ಯಾ ರಾವ್", "ಕಾವ್ಯಾ ರಾವ್"),
        ("പേര്: അനൂപ് നായർ", "അനൂപ് നായർ"),
        ("नाव: प्रिया शर्मा", "प्रिया शर्मा"),
        ("ନାମ: ଅନିଲ ଦାସ", "ଅନିଲ ଦାସ"),
        ("ਨਾਮ: ਹਰਪ੍ਰੀਤ ਸਿੰਘ", "ਹਰਪ੍ਰੀਤ ਸਿੰਘ"),
        ("பெயர்: குமார்", "குமார்"),
        ("పేరు: రవి కుమార్", "రవి కుమార్"),
    ]
    for text, value in examples:
        assert any(f.value == value and f.pii_type == "PERSON" for f in detect_ner(text)), text


def test_mobile_detects_spacing_and_hyphens():
    assert "MOBILE" in types("Contact: 98765 43210")
    assert "MOBILE" in types("Contact: 98765-43210")


def test_devanagari_mobile_digits_are_normalized():
    assert "MOBILE" in types("संपर्क: ९८७६५४३२१०")


def test_privacy_policy_recommends_redaction_for_direct_identifier():
    from detectors.base import Finding
    from detectors.privacy_policy import recommend_actions
    finding = Finding("PAN", 0, 10, .99, "ABCPE1234F", "regex", "high")
    result = recommend_actions([finding], {"level": "low", "combination_warning": False})
    assert result[0]["action"] == "redact"
    assert "ABCPE1234F" not in str(result)


def test_review_prioritization_returns_no_matched_values():
    from detectors.base import Finding
    from detectors.privacy_policy import prioritize_review
    finding = Finding("BANK_ACCOUNT", 10, 22, .52, "123456789012", "regex", "review")
    result = prioritize_review([finding], {"level": "high"})
    assert result and result[0]["priority"] > .5
    assert "123456789012" not in str(result)


def test_risk_score_explains_components_and_relation_categories_only():
    from detectors.contextual_risk import assess_privacy_risk
    from detectors.base import Finding
    text = "Ramesh works at ABC Hospital. He is a 42-year-old teacher in Sector 12."
    findings = [Finding("PERSON", 0, 6, .9, "Ramesh"), Finding("ORGANIZATION", 16, 29, .8, "ABC Hospital")]
    result = assess_privacy_risk(text, findings)
    assert "score_components" in result
    assert result["level"] == "high"
    assert "Ramesh" not in str(result["relationship_signals"])


def test_mutation_robustness_suite_has_ground_truth_and_negative_case():
    from evaluation import mutation_suite
    rows = mutation_suite()
    assert any(row["expected_type"] is None for row in rows)
    assert any(row["name"] == "mobile_devanagari_digits" for row in rows)
