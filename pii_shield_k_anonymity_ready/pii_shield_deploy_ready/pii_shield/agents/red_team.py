"""Red-team pass searches for residual detectable values and common OCR variants."""
from agents.verifier import residual_findings

def inspect(output, original_findings=()):
    residual=residual_findings(output)
    # Also check normalized known values without returning those values in the trace.
    extra=[]
    for f in original_findings:
        compact=''.join(ch for ch in f.value if ch.isalnum()).casefold()
        if len(compact)>=7:
            outcompact=''.join(ch for ch in output if ch.isalnum()).casefold()
            if compact in outcompact: extra.append(f)
    return {"verified":not residual and not extra,"residual_count":len(residual)+len(extra),"residual_types":sorted({f.pii_type for f in residual+extra}),"findings":residual}
