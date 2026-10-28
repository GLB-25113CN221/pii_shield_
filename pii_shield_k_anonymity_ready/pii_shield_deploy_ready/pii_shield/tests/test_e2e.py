from agents.orchestrator import process_text
def test_text_redaction():
    clean,report=process_text("Email: demo.user@example.com","txt")
    assert "demo.user@example.com" not in clean
    assert report["verification_status"]=="VERIFIED"
