#!/usr/bin/env bash
# One-command setup and run for NyayaLens (macOS / Linux).
set -e
cd "$(dirname "$0")"

PY=$(command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3 || true)
[ -z "$PY" ] && { echo "Python 3 is not installed. Install it from https://www.python.org/downloads/ and run this again."; exit 1; }

echo "==> Setting up the virtual environment"
[ -d venv ] || "$PY" -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
echo "==> Installing packages (first run takes a few minutes)"
pip install -q -r requirements.txt

if ! command -v tesseract >/dev/null 2>&1 && command -v brew >/dev/null 2>&1; then
  echo "==> Installing OCR tools for scanned files and card photos"
  HOMEBREW_NO_AUTO_UPDATE=1 brew install tesseract poppler || echo "   (OCR install skipped. Text-based files still work.)"
fi

lsof -ti:8000 2>/dev/null | xargs kill 2>/dev/null || true
( sleep 5; open http://127.0.0.1:8000 2>/dev/null || xdg-open http://127.0.0.1:8000 2>/dev/null || true ) &
echo "==> Starting NyayaLens at http://127.0.0.1:8000   (press Ctrl+C to stop)"
python run.py
