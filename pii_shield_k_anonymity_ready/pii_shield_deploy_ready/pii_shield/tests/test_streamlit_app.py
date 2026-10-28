"""Smoke test the UI when Streamlit is installed in the target environment."""
import pytest
from pathlib import Path
streamlit = pytest.importorskip('streamlit')
from streamlit.testing.v1 import AppTest

def test_app_starts_without_streamlit_exceptions():
    at=AppTest.from_file(str(Path(__file__).resolve().parent.parent/'app.py'),default_timeout=30).run()
    assert not at.exception, [e.message for e in at.exception]
