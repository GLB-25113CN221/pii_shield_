"""Synthetic detector evaluation (not representative of real-world performance)."""
from collections import defaultdict
from detectors.identifiers import detect_identifiers

def main():
    # 120 synthetic examples: 60 email positives and 60 negatives.
    samples=[]
    for i in range(60):
        samples.append((f"Contact demo{i}@example.com", {"EMAIL"}))
        samples.append((f"This is harmless synthetic sentence number {i}.", set()))
    stats=defaultdict(lambda: {"tp":0,"fp":0,"fn":0})
    for text, truth in samples:
        predicted={f.pii_type for f in detect_identifiers(text)}
        for kind in set().union(truth,predicted):
            if kind in truth and kind in predicted: stats[kind]["tp"]+=1
            elif kind in predicted: stats[kind]["fp"]+=1
            elif kind in truth: stats[kind]["fn"]+=1
    print(f"Synthetic evaluation: {len(samples)} samples (not a real-world benchmark)")
    for kind, s in sorted(stats.items()):
        precision=s['tp']/(s['tp']+s['fp']) if s['tp']+s['fp'] else 0.0
        recall=s['tp']/(s['tp']+s['fn']) if s['tp']+s['fn'] else 0.0
        print(f"{kind}: precision={precision:.3f}, recall={recall:.3f}, TP={s['tp']} FP={s['fp']} FN={s['fn']}")
if __name__=="__main__": main()
