"""Small reproducible synthetic evaluation; not a real-world benchmark."""
import random
from detectors.identifiers import detect_identifiers
from ner.multilingual import detect_ner
from agents.planner import ollama_available
from agents.context_reviewer import review

def synthetic_dataset(seed=42):
    rng=random.Random(seed)
    rows=[
      ("नाम: राजेश कुमार, ईमेल demo.user@example.com",[("PERSON","राजेश कुमार"),("EMAIL","demo.user@example.com")]),
      ("Name: Priya Sharma; PAN: ABCPE1234F",[("PERSON","Priya Sharma"),("PAN","ABCPE1234F")]),
      ("पता: १२, कमला नगर, दिल्ली",[("ADDRESS","१२, कमला नगर, दिल्ली")]),
      ("Mobile 9876543210 and IFSC HDFC0001234",[("MOBILE","9876543210"),("IFSC","HDFC0001234")]),
      ("Order ID 123456789012 and invoice 000000",[]),
      ("Name: River View Apartments; order number 555123",[]),
      ("GSTIN 27ABCPE1234F1Z5, voter ID ABC1234567",[("GSTIN","27ABCPE1234F1Z5"),("VOTER_ID","ABC1234567")]),
      ("OCR noise: emaiI demo.user@example.com; phone 98７6543210",[("EMAIL","demo.user@example.com")]),
      ("नाम राजेश कुमार, पता ४५ एमजी रोड पुणे",[("PERSON","राजेश कुमार"),("ADDRESS","४५ एमजी रोड पुणे")]),
      # Explicit-field examples cover IndicNER's 11 supported languages.
      ("নাম: ৰাহুল দাস",[("PERSON","ৰাহুল দাস")]),
      ("নাম: অনন্যা সেন",[("PERSON","অনন্যা সেন")]),
      ("નામ: આરવ પટેલ",[("PERSON","આરવ પટેલ")]),
      ("ಹೆಸರು: ಕಾವ್ಯಾ ರಾವ್",[("PERSON","ಕಾವ್ಯಾ ರಾವ್")]),
      ("പേര്: അനൂപ് നായർ",[("PERSON","അനൂപ് നായർ")]),
      ("ନାମ: ଅନିଲ ଦାସ",[("PERSON","ଅନିଲ ଦାସ")]),
      ("ਨਾਮ: ਹਰਪ੍ਰੀਤ ਸਿੰਘ",[("PERSON","ਹਰਪ੍ਰੀਤ ਸਿੰਘ")]),
      ("పేరు: రవి కుమార్",[("PERSON","రవి కుమార్")]),
      ("Ticket ref ABCDE12345, product code 1234567890",[]),
    ]
    # Small deterministic augmentation to keep synthetic data generation visible and reproducible.
    for i in range(5): rows.append((f"Reference order-{rng.randint(10000,99999)} for package",[]))
    return rows

def evaluate(mode="rule-only"):
    rows=synthetic_dataset(); by={}
    for text,gold in rows:
        found=detect_identifiers(text)+detect_ner(text)
        if mode=="agent" and ollama_available():
            reviewed=[]
            for f in found:
                if f.status in ("pending","review"):
                    try:
                        d=review(text,f)
                        if d["decision"]=="reject": continue
                    except Exception: pass
                reviewed.append(f)
            found=reviewed
        preds=[]
        for f in found:
            value=text[f.start:f.end]
            if value.strip(): preds.append((f.pii_type,value.strip()))
        types={t for t,v in gold}|{t for t,v in preds}
        for t in types:
            g={v for typ,v in gold if typ==t}; p={v for typ,v in preds if typ==t}
            item=by.setdefault(t,[0,0,0]); item[0]+=len(g&p); item[1]+=len(p-g); item[2]+=len(g-p)
    result={}
    for t,(tp,fp,fn) in by.items():
        precision=tp/(tp+fp) if tp+fp else 0; recall=tp/(tp+fn) if tp+fn else 0
        result[t]={"precision":round(precision,3),"recall":round(recall,3),"f1":round(2*precision*recall/(precision+recall),3) if precision+recall else 0,"tp":tp,"fp":fp,"fn":fn}
    return {"mode":mode,"synthetic_samples":len(rows),"metrics":result,"agent_available":ollama_available()}


def mutation_suite():
    """Deterministic robustness cases inspired by adversarial mutation testing.

    These are synthetic test cases, not evidence of production accuracy. Each
    case states the target category so the UI can report pass/fail per mutation.
    """
    return [
        {"name": "mobile_with_spaces", "text": "Contact: 98765 43210", "expected_type": "MOBILE"},
        {"name": "mobile_with_hyphens", "text": "Contact: 98765-43210", "expected_type": "MOBILE"},
        {"name": "mobile_devanagari_digits", "text": "संपर्क: ९८७६५४३२१०", "expected_type": "MOBILE"},
        {"name": "pan_without_label", "text": "ABCPE1234F", "expected_type": "PAN"},
        {"name": "email_in_sentence", "text": "Send the report to demo.user@example.com today", "expected_type": "EMAIL"},
        {"name": "ifsc_in_context", "text": "Branch IFSC HDFC0001234", "expected_type": "IFSC"},
        {"name": "hindi_name_label", "text": "नाम: राजेश कुमार", "expected_type": "PERSON"},
        {"name": "tamil_name_label", "text": "பெயர்: குமார்", "expected_type": "PERSON"},
        {"name": "gujarati_name_label", "text": "નામ: આરવ પટેલ", "expected_type": "PERSON"},
        {"name": "negative_order_number", "text": "Order ID 123456789012 and invoice 000000", "expected_type": None},
    ]


def evaluate_robustness():
    """Run a small deterministic smoke benchmark across known mutation cases."""
    from detectors.identifiers import detect_identifiers
    from ner.multilingual import detect_ner
    rows = mutation_suite()
    results = []
    passed = 0
    for row in rows:
        text = row["text"]
        found = detect_identifiers(text) + detect_ner(text)
        types = sorted({f.pii_type for f in found})
        expected = row["expected_type"]
        ok = (expected is None and not found) or (expected is not None and expected in types)
        passed += int(ok)
        results.append({"case": row["name"], "expected_type": expected, "detected_types": types, "pass": ok})
    return {
        "kind": "synthetic_mutation_smoke_test",
        "passed": passed,
        "total": len(rows),
        "pass_rate": round(passed / len(rows), 3) if rows else 0.0,
        "results": results,
        "warning": "Synthetic smoke tests are not a real-world benchmark; IndicNER results depend on model availability.",
    }
