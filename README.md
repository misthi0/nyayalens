# NyayaLens: Legal Document Analyser

Upload a legal document (contract, court paper, marriage certificate, stamp paper, Aadhaar, PAN) and get
the important details, clauses, risks and keywords back as a PDF report.

## Features
- Register / login (JWT, PBKDF2 password hashing)
- Upload PDF, DOCX, TXT, JPG, PNG (OCR for scans and photos)
- ML document-type classifier (TF-IDF + Logistic Regression)
- Extraction: parties, dates, amounts, case and registration numbers, law sections, emails, phones
- Reads the **full Aadhaar number (with checksum check), VID, PAN number**, name, father's name, date of birth and gender, shown on an ID-card panel with copy and hide buttons
- Clause detection (14 clause types) with plain-language risk notes and a 0-100 risk score
- Important-words highlighting, summary, PDF report, report history (open / download / delete)
- Uploaded files are never stored; only the analysis result is saved. Note that results contain the full ID numbers, so keep your database private

## Project layout
```
nyayalens/
├── app/
│   ├── main.py          FastAPI routes + serves the UI
│   ├── auth.py          password hashing, JWT
│   ├── database.py, models.py, schemas.py, config.py
│   └── ml/
│       ├── readers.py     PDF / DOCX / image -> text (OCR fallback)
│       ├── classifier.py  loads the trained model
│       ├── extractor.py   entities, clauses, keywords, risk, summary
│       ├── pipeline.py    ties everything together
│       └── report.py      PDF report (ReportLab)
├── ml_training/
│   ├── generate_data.py   synthetic starter dataset
│   └── train_classifier.py
├── frontend/index.html    the UI
├── sample_docs/           files to try
├── tests/                 pytest suite
├── Dockerfile, requirements.txt, run.py
```

## Run it with one command (macOS / Linux)
```bash
bash start.sh
```
That creates the environment, installs everything, opens the browser and starts the server.

## Run it manually (macOS / Linux)
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
brew install tesseract poppler      # optional, only needed for OCR of scans / photos
cp .env.example .env                # then set SECRET_KEY (export it, or use your shell profile)
python run.py                       # opens on http://127.0.0.1:8000
```
The classifier trains itself on first start. To retrain manually: `python -m ml_training.train_classifier`.
Run the tests with `pytest`. Interactive API docs are at `/docs`.

## API
| Method | Path | Purpose |
|---|---|---|
| POST | /api/auth/register, /api/auth/login | returns a bearer token |
| POST | /api/analyze | multipart `file` (+ optional `doc_type`) |
| GET | /api/reports, /api/reports/{id} | history, one report |
| GET | /api/reports/{id}/pdf | PDF download |
| DELETE | /api/reports/{id} | delete a report |

## How the ML works
1. **Read**: text extraction, with OCR when a PDF or image has no selectable text.
2. **Classify**: TF-IDF (1-2 grams) + Logistic Regression. Aadhaar and PAN formats are also checked by pattern. PAN reading tolerates common OCR mix-ups (0/O, 1/I, 5/S, 8/B).
3. **Extract**: regex layer for Indian formats, label-based name capture, organisation pattern.
4. **Clauses and risk**: clause library with weights, snippet of the matching sentence, score = sum of weights.
5. **Report**: ReportLab PDF.

## Honest limitations (read before your demo or viva)
- The starter classifier is trained on **synthetic** text, so its scores look better than real-world accuracy will.
  Train on real labelled documents with `--csv your_data.csv` (columns `text,label`) and report results on a held-out set.
- Extraction is rule-based. A good next step is a trained NER model (spaCy or InLegalBERT) and semantic clause
  matching with sentence-transformers (all-MiniLM-L6-v2), which you already use in your notebooks.
- Aadhaar and PAN are sensitive. Use only documents you are allowed to process, keep the database private, and use HTTPS in production.
- Output is a machine summary, not legal advice.

## Ideas to extend
Hindi OCR (`tesseract-ocr-hin`), clause comparison between two contracts, Q&A over a contract with RAG (Pinecone),
email alerts for court dates, role-based admin dashboard, PostgreSQL + Alembic migrations.
