"""Sentence-level clause detector: TF-IDF + one-vs-rest Logistic Regression trained on CUAD labels."""
import re

import joblib

from ..config import BASE_DIR
from .extractor import CLAUSES

CLAUSE_MODEL_PATH = BASE_DIR / "models" / "clause_model.joblib"
APPLIES_TO = {"Business agreement", "Stamp paper"}

# CUAD label -> name shown in the app (same names as the rule library where they overlap)
CATEGORIES = {
    "Governing Law": "Jurisdiction", "Anti-Assignment": "Assignment", "Cap On Liability": "Limitation of liability",
    "Termination For Convenience": "Termination", "Exclusivity": "Exclusivity", "Non-Compete": "Non-compete",
    "Liquidated Damages": "Penalty / liquidated damages", "Renewal Term": "Renewal term", "Audit Rights": "Audit rights",
    "Insurance": "Insurance", "Ip Ownership Assignment": "IP ownership", "Change Of Control": "Change of control",
    "Uncapped Liability": "Unlimited liability", "Covenant Not To Sue": "Covenant not to sue",
}
# clauses the rule library does not know: (risk weight 1-3, plain-language note)
ML_ONLY = {
    "Renewal term": (1, "Shows how long the contract renews for. Check the dates."),
    "Audit rights": (1, "One side may inspect the other's records."),
    "Insurance": (1, "A party must carry insurance. Check the cover required."),
    "IP ownership": (2, "Ownership of intellectual property is being assigned."),
    "Change of control": (2, "A sale or takeover can trigger rights, such as termination."),
    "Unlimited liability": (3, "Liability is not capped, so losses could be very large."),
    "Covenant not to sue": (2, "A party agrees not to bring certain legal claims."),
}
_model = None


def sentence_spans(text: str, min_len: int = 40, max_len: int = 900) -> list[tuple[int, int]]:
    bounds, start = [], 0
    for m in re.finditer(r"(?<=[.;])\s+|\n+", text):
        bounds.append((start, m.start()))
        start = m.end()
    bounds.append((start, len(text)))
    out = []
    for s, e in bounds:
        while e - s > max_len:  # split very long passages
            cut = text.rfind(" ", s, s + max_len)
            cut = cut if cut > s + 200 else s + max_len
            out.append((s, cut))
            s = cut + 1
        if e - s >= min_len:
            out.append((s, e))
    return out


def load():
    global _model
    if _model is None and CLAUSE_MODEL_PATH.exists():
        _model = joblib.load(CLAUSE_MODEL_PATH)
    return _model


def predict(text: str, max_sents: int = 3000):
    m = load()
    if m is None:
        return None
    sents = [text[s:e].strip() for s, e in sentence_spans(text)[:max_sents]]
    if not sents:
        return {"best": {}, "n": 0, "threshold": m["threshold"]}
    P = m["clf"].predict_proba(m["vec"].transform(sents))
    best = {}
    for k, (_, display) in enumerate(m["cats"]):
        j = int(P[:, k].argmax())
        if P[j, k] >= m["threshold"]:
            best[display] = (float(P[j, k]), sents[j])
    return {"best": best, "n": len(sents), "threshold": m["threshold"]}


def merge(doc_type: str, text: str, clauses: list[dict]):
    info = {"used": False, "model": "TF-IDF + one-vs-rest Logistic Regression (trained on CUAD contracts)"}
    if doc_type not in APPLIES_TO:
        info["reason"] = "Used for business agreements and stamp papers only."
        return clauses, info
    res = predict(text)
    if res is None:
        info["reason"] = "Not trained yet. Run: python -m ml_training.train_clauses"
        return clauses, info
    by_name = {c["name"]: c for c in clauses}
    for c in clauses:
        c["source"] = "rules"
    found = []
    for name, (p, snip) in res["best"].items():
        found.append({"name": name, "prob": round(p * 100, 1)})
        if name in by_name:
            by_name[name]["source"] = "rules+ML"
            by_name[name]["ml_score"] = round(p, 3)
        else:
            w, why = ML_ONLY[name] if name in ML_ONLY else CLAUSES[name][1:]
            clauses.append({"name": name, "risk": w, "explanation": why, "source": "ML", "ml_score": round(p, 3),
                            "snippet": snip if len(snip) <= 240 else snip[:237] + "..."})
    info.update({"used": True, "threshold": res["threshold"], "sentences_scanned": res["n"],
                 "found": sorted(found, key=lambda x: -x["prob"])})
    return sorted(clauses, key=lambda c: -c["risk"]), info
