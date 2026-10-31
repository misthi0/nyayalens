"""Show how the ML models work, step by step, in the terminal.

  python -m ml_training.demo sample_docs/business_agreement.txt
"""
import sys
from pathlib import Path

from app.ml.pipeline import analyze_document

f = Path(sys.argv[1] if len(sys.argv) > 1 else "sample_docs/business_agreement.txt")
r = analyze_document(f.name, f.read_bytes())
c, k = r["ml"]["classifier"], r["ml"]["clause_model"]
print(f"\nFILE: {f.name}  ({r['word_count']} words, read with: {r['extraction_method']})")
print("\nSTEP 1 - Document classifier (TF-IDF + Logistic Regression)")
for x in c["probs"][:5]:
    print(f"   {x['label']:22s} {'#' * int(x['p'] / 4):25s} {x['p']}%")
print(f"   -> decision: {r['doc_type']}")
print(f"\nSTEP 2 - Why? Words that pushed the model toward '{c['explained_class']}'")
print("   " + ", ".join(f"{w['term']} ({w['weight']})" for w in c["top_words"]))
print("\nSTEP 3 - Clause detector (trained on CUAD contracts)")
if k.get("used"):
    print(f"   scanned {k['sentences_scanned']} sentences, kept scores >= {k['threshold']}")
    for x in k["found"]:
        print(f"   {x['name']:30s} {x['prob']}%")
else:
    print("   not used:", k.get("reason"))
print("\nSTEP 4 - Rules (regex patterns, checksum, keyword weights)")
print(f"   {len(r['entities'])} details extracted | {len(r['clauses'])} clauses | risk {r['risk']['score']}/100 ({r['risk']['level']})\n")
