import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_MINUTES = int(os.getenv("TOKEN_MINUTES", "720"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'nyayalens.db'}")
MODEL_PATH = BASE_DIR / "models" / "doc_classifier.joblib"
MAX_UPLOAD_MB = 10
ALLOWED_EXT = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"}
OTHER = "Other document"
UNSURE_BELOW = 0.55  # below this confidence the app asks the user to choose the type
DOC_TYPES = ["Business agreement", "Court paper", "Marriage certificate",
             "Stamp paper", "Aadhaar card", "PAN card"]
