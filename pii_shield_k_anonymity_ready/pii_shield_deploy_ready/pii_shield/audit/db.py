"""PII-free SQLite audit log with 365-day retention."""
import sqlite3, time, uuid
from config import AUDIT_DB, AUDIT_RETENTION_DAYS
def connect():
    db=sqlite3.connect(AUDIT_DB)
    db.execute("""CREATE TABLE IF NOT EXISTS audit(
      timestamp REAL, document_id TEXT, file_type TEXT, language TEXT,
      detected_types TEXT, counts TEXT, verification_status TEXT, risk_score INTEGER)""")
    db.execute("DELETE FROM audit WHERE timestamp < ?",(time.time()-AUDIT_RETENTION_DAYS*86400,))
    db.commit(); return db
def log_event(file_type,language,findings,verification_status,risk_score):
    import json
    document_id=str(uuid.uuid4())
    counts={}
    for f in findings: counts[f.pii_type]=counts.get(f.pii_type,0)+1
    db=connect()
    db.execute("INSERT INTO audit VALUES(?,?,?,?,?,?,?,?)",(time.time(),document_id,file_type,language,json.dumps(sorted(counts)),json.dumps(counts),verification_status,risk_score))
    db.commit(); db.close()
    return document_id
def rows():
    db=connect(); data=db.execute("SELECT timestamp,document_id,file_type,language,detected_types,counts,verification_status,risk_score FROM audit ORDER BY timestamp DESC").fetchall(); db.close(); return data
