"""Download REAL legal text from GitHub, mix it with synthetic samples, and write data.csv."""
import csv
import io
import json
import random
import re
import urllib.request
import zipfile

from .generate_data import MAKERS, noisy

CUAD_ZIP = "https://raw.githubusercontent.com/TheAtticusProject/cuad/main/data.zip"
COURT_URLS = [f"https://raw.githubusercontent.com/OpenNyAI/Opennyai/master/{p}" for p in (
    "samples/sample_judgment1.txt", "samples/sample_judgment2.txt",
    "tests/examples/judgement_texts/811682.txt", "tests/examples/judgement_texts/72703592.txt")]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "nyayalens-data-collector"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def window(text, rnd, start=None, size=(600, 1500)):
    n = rnd.randint(*size)
    s = 0 if start is None else start
    if start is None and len(text) > n:
        s = rnd.randint(0, len(text) - n)
    chunk = text[s:s + n]
    return chunk[chunk.find(" ") + 1:] if s else chunk


def clean(t):
    return re.sub(r"\s+", " ", t.replace("\x00", " ")).strip()


def main(out="data.csv", seed=11):
    rnd = random.Random(seed)
    rows = []  # text, label, group, source
    print("Downloading CUAD contracts ...")
    with zipfile.ZipFile(io.BytesIO(fetch(CUAD_ZIP))) as z:
        name = next(n for n in z.namelist() if n.endswith("CUADv1.json"))
        contracts = json.loads(z.read(name))["data"]
    for i, c in enumerate(contracts):
        text = clean(c["paragraphs"][0]["context"])
        if len(text) < 800:
            continue
        w = noisy(rnd, window(text, rnd, start=0 if i % 2 == 0 else None), level=rnd.choice([0, 0, 0, 0.03, 0.06]))
        rows.append((w, "Business agreement", c["title"], "real:CUAD"))
    print(f"  {len(rows)} contract excerpts")
    n_court = 0
    for url in COURT_URLS:
        try:
            text = clean(fetch(url).decode("utf-8", errors="ignore"))
        except Exception as e:
            print("  skipped", url.split("/")[-1], "-", e)
            continue
        for _ in range(12):
            rows.append((noisy(rnd, window(text, rnd), level=rnd.choice([0, 0, 0, 0.03, 0.06])), "Court paper", url.split("/")[-1], "real:OpenNyAI"))
            n_court += 1
    print(f"  {n_court} court-judgment excerpts")
    for label, fn in MAKERS.items():
        k = 100 if label in ("Business agreement", "Court paper") else 150
        for j in range(k):
            rows.append((noisy(rnd, fn(rnd)), label, f"syn-{label}-{j}", "synthetic"))
    rnd.shuffle(rows)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["text", "label", "group", "source"])
        w.writerows(rows)
    from collections import Counter
    print(f"Wrote {len(rows)} rows to {out}")
    for (lab, src), n in sorted(Counter((r[1], r[3]) for r in rows).items()):
        print(f"  {lab:22s} {src:15s} {n}")


if __name__ == "__main__":
    main()
