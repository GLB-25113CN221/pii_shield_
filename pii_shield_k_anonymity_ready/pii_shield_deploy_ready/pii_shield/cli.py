"""CLI: python cli.py INPUT OUTPUT"""
import sys
from pathlib import Path
from agents.orchestrator import process_text
def main():
    if len(sys.argv)!=3: raise SystemExit("Usage: python cli.py INPUT OUTPUT")
    src,dst=map(Path,sys.argv[1:])
    if src.stat().st_size>20*1024*1024: raise SystemExit("File exceeds 20 MB limit.")
    text=src.read_text(encoding="utf-8",errors="replace")
    clean,report=process_text(text,src.suffix.lstrip("."))
    dst.write_text(clean,encoding="utf-8")
    print(f"Sanitized output written. Verification: {report['verification_status']}; risk: {report['risk_score']}/100")
if __name__=="__main__": main()
