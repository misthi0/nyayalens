from pathlib import Path

from app.ml.pipeline import analyze_document, ensure_model

DOCS = Path(__file__).resolve().parent.parent / "sample_docs"


def test_classifier_explanation():
    ensure_model()
    out = analyze_document("court_order.txt", (DOCS / "court_order.txt").read_bytes())
    ml = out["ml"]["classifier"]
    assert abs(sum(p["p"] for p in ml["probs"]) - 100) < 1
    assert ml["explained_class"] == "Court paper" and len(ml["top_words"]) > 0


def test_clause_model_is_optional_but_reported():
    ensure_model()
    out = analyze_document("b.txt", (DOCS / "business_agreement.txt").read_bytes())
    info = out["ml"]["clause_model"]
    assert "used" in info
    if info["used"]:
        assert info["sentences_scanned"] > 0
