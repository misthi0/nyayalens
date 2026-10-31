import io
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import auth, config
from .database import Base, engine, get_db
from .ml.pipeline import analyze_document, ensure_model
from .ml.report import build_pdf
from .models import Report, User
from .schemas import LoginIn, RegisterIn


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    ensure_model()
    yield


app = FastAPI(title="NyayaLens", version="1.0.0", lifespan=lifespan)


def _session(user: User) -> dict:
    return {"access_token": auth.create_token(user.id), "name": user.name}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "This email is already registered. Log in instead")
    user = User(name=body.name.strip(), email=body.email, password_hash=auth.hash_password(body.password))
    db.add(user)
    db.commit()
    return _session(user)


@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not auth.verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect")
    return _session(user)


@app.get("/api/me")
def me(user: User = Depends(auth.current_user)):
    return {"name": user.name, "email": user.email}


@app.post("/api/analyze")
def analyze(file: UploadFile = File(...), doc_type: str | None = Form(None),
            user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.ALLOWED_EXT:
        raise HTTPException(415, f"Unsupported file type. Use: {', '.join(sorted(config.ALLOWED_EXT))}")
    if doc_type and doc_type not in config.DOC_TYPES:
        raise HTTPException(400, "Unknown document type")
    data = file.file.read(config.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if not data:
        raise HTTPException(400, "The file is empty")
    if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File is larger than {config.MAX_UPLOAD_MB} MB")
    try:
        result = analyze_document(file.filename, data, doc_type)
    except ValueError as e:
        raise HTTPException(422, str(e))
    row = Report(user_id=user.id, filename=file.filename, doc_type=result["doc_type"],
                 confidence=result["confidence"], risk_level=result["risk"]["level"], result=json.dumps(result))
    db.add(row)
    db.commit()
    result["id"] = row.id
    return result


def _owned(db: Session, user: User, rid: int) -> Report:
    row = db.get(Report, rid)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "Report not found")
    return row


@app.get("/api/reports")
def list_reports(user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Report).where(Report.user_id == user.id).order_by(Report.id.desc()).limit(50))
    return [{"id": r.id, "filename": r.filename, "doc_type": r.doc_type, "confidence": r.confidence,
             "risk_level": r.risk_level, "created_at": r.created_at.isoformat()} for r in rows]


@app.get("/api/reports/{rid}")
def get_report(rid: int, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    row = _owned(db, user, rid)
    return {**json.loads(row.result), "id": row.id}


@app.get("/api/reports/{rid}/pdf")
def report_pdf(rid: int, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    row = _owned(db, user, rid)
    pdf = build_pdf(json.loads(row.result))
    name = f"NyayaLens-{row.doc_type.replace(' ', '-')}-{row.id}.pdf"
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.delete("/api/reports/{rid}")
def delete_report(rid: int, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    db.delete(_owned(db, user, rid))
    db.commit()
    return {"deleted": rid}


app.mount("/", StaticFiles(directory=config.BASE_DIR / "frontend", html=True), name="ui")
