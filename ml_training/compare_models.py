"""Compare classifiers on the same data (grouped 5-fold cross-validation). Saves reports/model_comparison.txt"""
import time

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from app.config import BASE_DIR

df = pd.read_csv(BASE_DIR / "data.csv")
X, y, g = df["text"].astype(str).tolist(), df["label"].tolist(), df["group"].astype(str).tolist()
MODELS = {"Naive Bayes (Complement)": ComplementNB(),
          "Linear SVM": LinearSVC(class_weight="balanced"),
          "Logistic Regression (used)": LogisticRegression(max_iter=1000, C=5, class_weight="balanced")}
lines = [f"{'Model':30s} {'Accuracy':>10s} {'Macro F1':>10s} {'Time (s)':>9s}", "-" * 63]
for name, clf in MODELS.items():
    pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)), ("clf", clf)])
    t = time.time()
    r = cross_validate(pipe, X, y, groups=g, cv=GroupKFold(n_splits=5), scoring=["accuracy", "f1_macro"])
    lines.append(f"{name:30s} {r['test_accuracy'].mean():10.3f} {r['test_f1_macro'].mean():10.3f} {time.time() - t:9.1f}")
out = "\n".join(lines)
print(out)
(BASE_DIR / "reports").mkdir(exist_ok=True)
(BASE_DIR / "reports" / "model_comparison.txt").write_text(out, encoding="utf-8")
