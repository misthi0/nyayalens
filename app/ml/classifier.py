import joblib
from ..config import MODEL_PATH

_model = None


def load():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def reload():
    global _model
    _model = None
    return load()


def predict_proba(text: str) -> dict[str, float]:
    m = load()
    return dict(zip(m.classes_, map(float, m.predict_proba([text])[0])))


def predict(text: str) -> tuple[str, float]:
    probs = predict_proba(text)
    label = max(probs, key=probs.get)
    return label, probs[label]


def explain(text: str, cls: str, k: int = 8) -> list[dict]:
    """Which words pushed the model toward `cls` (TF-IDF value x learned weight)."""
    m = load()
    vec, clf = m.named_steps["tfidf"], m.named_steps["clf"]
    classes = list(clf.classes_)
    if cls not in classes:
        return []
    i = classes.index(cls)
    x = vec.transform([text]).tocsr()
    names = vec.get_feature_names_out()
    pairs = [(names[j], float(v * clf.coef_[i][j])) for j, v in zip(x.indices, x.data)]
    pairs = sorted((p for p in pairs if p[1] > 0), key=lambda p: -p[1])
    return [{"term": t, "weight": round(w, 3)} for t, w in pairs[:k]]
