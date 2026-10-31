from datetime import datetime

from .. import config
from . import classifier, clause_model, extractor as ex
from .readers import extract_text


def ensure_model():
    """Train the starter classifier on first run if no saved model exists."""
    if not config.MODEL_PATH.exists():
        from ml_training.train_classifier import train
        train(quiet=True)


def classify(text: str, hint: str | None) -> tuple[str, float, list[str]]:
    notes = []
    probs = classifier.predict_proba(text)
    top = max(probs, key=probs.get)
    if hint:
        if top != hint and probs[top] > 0.5:
            what = "like it is not a legal document" if top == config.OTHER else f"more like {top.lower()}"
            notes.append(f"You chose {hint}, but the text looks {what}.")
        return hint, probs.get(hint, 0.0), notes
    if len(text) < 1500:  # IDs have a strict format, so trust the pattern over the model
        if ex.find_pans(text):
            return "PAN card", 0.99, notes
        if ex.find_aadhaar(text):
            return "Aadhaar card", 0.99, notes
    return top, probs[top], notes


def build_id_card(doc_type: str, text: str, ents: list[dict]) -> dict | None:
    if doc_type not in ("Aadhaar card", "PAN card"):
        return None
    first = lambda t: next((e["value"] for e in ents if e["type"] == t), None)
    aad = doc_type == "Aadhaar card"
    num = first("Aadhaar number" if aad else "PAN number")
    return {"kind": "Aadhaar" if aad else "PAN", "number": num, "name": first("Name"), "father": first("Father's name"),
            "dob": first("Date of birth") or first("Date"), "gender": first("Gender"), "vid": first("VID") if aad else None,
            "valid": ex.verhoeff_ok(num.replace(" ", "")) if aad and num else None}


def analyze_document(filename: str, data: bytes, hint: str | None = None) -> dict:
    text, method = extract_text(filename, data)
    if len(text.strip()) < 15:
        raise ValueError("No readable text found in this file.")
    doc_type, conf, notes = classify(text, hint)
    uncertain = hint is None and conf < config.UNSURE_BELOW
    if uncertain:
        notes.append(f"Low confidence ({conf * 100:.0f}%). Choose the document kind yourself and analyse again.")
    if doc_type == config.OTHER:
        notes.append("This does not look like a legal document, so clause checks were skipped.")
    ents = ex.extract_entities(text)
    clauses = ex.extract_clauses(text) if doc_type in ex.CLAUSE_TYPES else []
    clauses, clause_ml = clause_model.merge(doc_type, text, clauses)
    risk = ex.risk_score(clauses) if clauses or doc_type in ex.CLAUSE_TYPES else {"score": 0, "level": "n/a"}
    flags = notes + [f"{c['name']}: {c['explanation']}" for c in clauses if c["risk"] >= 2]
    if doc_type == "Court paper" and any(e["type"] == "Date" for e in ents):
        flags.append("Court dates found. Add them to your calendar and confirm with your lawyer.")
    probs = classifier.predict_proba(text)
    cls = doc_type if doc_type in probs else max(probs, key=probs.get)
    ml_info = {"classifier": {"model": "TF-IDF + Logistic Regression", "explained_class": cls,
                              "probs": [{"label": k, "p": round(v * 100, 1)} for k, v in sorted(probs.items(), key=lambda x: -x[1])],
                              "top_words": classifier.explain(text, cls)},
               "clause_model": clause_ml}
    id_card = build_id_card(doc_type, text, ents)
    if id_card:
        if not id_card["number"]:
            flags.append(f"No {id_card['kind']} number was found. Upload a clearer, straight-on scan or photo.")
        elif id_card["valid"] is False:
            flags.append("This Aadhaar number fails the checksum, so a digit may have been misread. Compare it with your card.")
    return {
        "ml": ml_info, "id_card": id_card, "uncertain": uncertain, "filename": filename, "doc_type": doc_type, "confidence": round(conf * 100, 1),
        "extraction_method": method, "word_count": len(text.split()),
        "summary": ex.summarise(doc_type, text, ents, clauses), "keywords": ex.keywords(text),
        "entities": ents, "clauses": clauses, "risk": risk, "flags": flags,
        "generated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }
