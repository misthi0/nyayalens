"""Train the document-type classifier (TF-IDF + Logistic Regression).

  python -m ml_training.train_classifier                 # synthetic starter data
  python -m ml_training.train_classifier --csv data.csv  # your own data: columns text,label
"""
import argparse

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.config import MODEL_PATH
from .generate_data import generate


def train(csv: str | None = None, quiet: bool = False):
    groups = None
    if csv:
        import pandas as pd
        df = pd.read_csv(csv)
        texts, labels = df["text"].astype(str).tolist(), df["label"].tolist()
        if "group" in df:
            groups = df["group"].astype(str).tolist()
    else:
        texts, labels = generate()
    if groups:
        from sklearn.model_selection import GroupShuffleSplit
        tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42).split(texts, labels, groups))
        Xtr, ytr = [texts[i] for i in tr], [labels[i] for i in tr]
        Xte, yte = [texts[i] for i in te], [labels[i] for i in te]
    else:
        Xtr, Xte, ytr, yte = train_test_split(texts, labels, test_size=0.2, stratify=labels, random_state=42)
    pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)),
                     ("clf", LogisticRegression(max_iter=1000, C=5, class_weight="balanced"))])
    pipe.fit(Xtr, ytr)
    if not quiet:
        print(classification_report(yte, pipe.predict(Xte)))
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    if not quiet:
        print("Saved model to", MODEL_PATH)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    train(ap.parse_args().csv)
