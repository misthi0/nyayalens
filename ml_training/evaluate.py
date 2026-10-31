"""Evidence for your teacher: metrics, confusion matrix, cross-validation, learned words, live predictions."""
import os
import time

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_val_score
from sklearn.pipeline import Pipeline

from app.config import BASE_DIR, MODEL_PATH

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = BASE_DIR / "reports"
OUT.mkdir(exist_ok=True)
lines = []


def say(s=""):
    print(s)
    lines.append(s)


df = pd.read_csv(BASE_DIR / "data.csv")
texts, labels = df["text"].astype(str).tolist(), df["label"].tolist()
groups = df["group"].astype(str).tolist() if "group" in df else list(range(len(df)))
model = joblib.load(MODEL_PATH)

say("NYAYALENS - MODEL EVALUATION REPORT")
say("=" * 60)
say(f"Model file : {MODEL_PATH.name}  ({os.path.getsize(MODEL_PATH) / 1024:.0f} KB, trained {time.ctime(os.path.getmtime(MODEL_PATH))})")
say("Algorithm  : TF-IDF (1-2 word n-grams) + Logistic Regression")
say(f"Dataset    : {len(df)} samples, {df['label'].nunique()} classes")
if "source" in df:
    for (lab, src), n in df.groupby(["label", "source"]).size().items():
        say(f"   {lab:22s} {src:15s} {n}")

tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42).split(texts, labels, groups))
overlap = {groups[i] for i in tr} & {groups[i] for i in te}
Xte, yte = [texts[i] for i in te], [labels[i] for i in te]
pred = model.predict(Xte)
say()
say(f"1) HELD-OUT TEST  ({len(te)} samples from documents not used in training; shared documents: {len(overlap)})")
say(f"   Accuracy {accuracy_score(yte, pred):.3f} | Macro F1 {f1_score(yte, pred, average='macro'):.3f}")
say(classification_report(yte, pred, zero_division=0))

classes = list(model.classes_)
cm = confusion_matrix(yte, pred, labels=classes)
fig, ax = plt.subplots(figsize=(8, 7))
ConfusionMatrixDisplay(cm, display_labels=classes).plot(ax=ax, xticks_rotation=35, colorbar=False, cmap="Blues")
ax.set_title("Confusion matrix (held-out test set)")
plt.tight_layout()
plt.savefig(OUT / "confusion_matrix.png", dpi=150)
say("   Confusion matrix image saved: reports/confusion_matrix.png")

say()
say("2) 5-FOLD CROSS-VALIDATION (grouped by document)")
pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)),
                 ("clf", LogisticRegression(max_iter=1000, C=5, class_weight="balanced"))])
cv = cross_val_score(pipe, texts, labels, groups=groups, cv=GroupKFold(n_splits=5), scoring="accuracy")
say(f"   Fold accuracies: {np.round(cv, 3).tolist()}")
say(f"   Mean {cv.mean():.3f} +/- {cv.std():.3f}")

say()
say("3) WHAT THE MODEL LEARNED (words that push toward each class)")
names = np.array(model.named_steps["tfidf"].get_feature_names_out())
coef = model.named_steps["clf"].coef_
for i, c in enumerate(classes):
    say(f"   {c:22s}: " + ", ".join(names[np.argsort(coef[i])[-8:][::-1]]))

say()
say("4) LIVE PREDICTIONS ON SAMPLE FILES")
for f in sorted((BASE_DIR / "sample_docs").glob("*.txt")):
    t = f.read_text(encoding="utf-8", errors="ignore")
    p = model.predict_proba([t])[0]
    say(f"   {f.name:26s} -> {classes[p.argmax()]:20s} ({p.max() * 100:.1f}%)")

say()
say("NOTE: Most classes include synthetic data and classes look very different, so scores are")
say("optimistic. Real-world accuracy must be measured on new, real documents.")
(OUT / "model_report.txt").write_text("\n".join(lines), encoding="utf-8")
print("\nSaved: reports/model_report.txt and reports/confusion_matrix.png")
