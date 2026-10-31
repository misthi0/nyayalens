"""Train the clause detector on CUAD (real, expert-labelled contracts). Downloads ~18 MB from GitHub.

  python -m ml_training.train_clauses
"""
import io
import json
import random
import urllib.request
import zipfile

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import GroupShuffleSplit
from sklearn.multiclass import OneVsRestClassifier

from app.config import BASE_DIR
from app.ml.clause_model import CATEGORIES, CLAUSE_MODEL_PATH, sentence_spans

CUAD_ZIP = "https://raw.githubusercontent.com/TheAtticusProject/cuad/main/data.zip"
THRESHOLD = 0.7


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "nyayalens"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def build(contracts):
    names = list(CATEGORIES)
    texts, rows, groups = [], [], []
    for c in contracts:
        para = c["paragraphs"][0]
        ctx = para["context"]
        ans = {n: [] for n in names}
        for q in para["qas"]:
            cat = q["id"].split("__")[-1]
            if cat in ans:
                ans[cat] += [(a["answer_start"], a["answer_start"] + len(a["text"])) for a in q["answers"]]
        for s, e in sentence_spans(ctx):
            row = np.zeros(len(names), dtype=np.int8)
            for k, n in enumerate(names):
                for a0, a1 in ans[n]:
                    ov = min(e, a1) - max(s, a0)
                    if ov >= 20 and (ov / (e - s) >= 0.5 or ov / (a1 - a0) >= 0.5):
                        row[k] = 1
                        break
            texts.append(ctx[s:e].strip())
            rows.append(row)
            groups.append(c["title"])
    return texts, np.array(rows), np.array(groups)


def main():
    rnd = random.Random(5)
    print("Downloading CUAD ...")
    with zipfile.ZipFile(io.BytesIO(fetch(CUAD_ZIP))) as z:
        name = next(n for n in z.namelist() if n.endswith("CUADv1.json"))
        contracts = json.loads(z.read(name))["data"]
    texts, Y, groups = build(contracts)
    print(f"{len(contracts)} contracts -> {len(texts)} sentences, {int(Y.sum())} labelled clause sentences")

    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42).split(texts, Y, groups))
    keep = [i for i in tr if Y[i].any() or rnd.random() < 0.15]  # all clauses + 15% of other sentences
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=60000, sublinear_tf=True)
    Xtr = vec.fit_transform([texts[i] for i in keep])
    clf = OneVsRestClassifier(LogisticRegression(max_iter=300, C=4, class_weight="balanced", solver="liblinear"))
    clf.fit(Xtr, Y[keep])

    P = clf.predict_proba(vec.transform([texts[i] for i in te]))
    Yte = Y[te]
    lines = [f"CLAUSE MODEL - held-out test on {len(set(groups[te]))} contracts the model never saw ({len(te)} sentences)",
             f"{'Clause':32s} {'Precision':>9s} {'Recall':>7s} {'F1':>6s} {'Examples':>9s}"]
    for thr in (0.5, THRESHOLD):
        pr, rc, f1, _ = precision_recall_fscore_support(Yte, (P >= thr).astype(int), zero_division=0)
        if thr == THRESHOLD:
            for k, n in enumerate(CATEGORIES.values()):
                lines.append(f"{n:32s} {pr[k]:9.2f} {rc[k]:7.2f} {f1[k]:6.2f} {int(Yte[:, k].sum()):9d}")
        lines.append(f"-- threshold {thr}: macro precision {pr.mean():.2f} | macro recall {rc.mean():.2f} | macro F1 {f1.mean():.2f}")
    out = "\n".join(lines)
    print(out)
    (BASE_DIR / "reports").mkdir(exist_ok=True)
    (BASE_DIR / "reports" / "clause_model_report.txt").write_text(out, encoding="utf-8")
    CLAUSE_MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"vec": vec, "clf": clf, "cats": list(CATEGORIES.items()), "threshold": THRESHOLD}, CLAUSE_MODEL_PATH)
    print("Saved model to", CLAUSE_MODEL_PATH)


if __name__ == "__main__":
    main()
