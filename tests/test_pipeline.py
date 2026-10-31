from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml import extractor as ex
from app.ml.pipeline import analyze_document, ensure_model

DOCS = Path(__file__).resolve().parent.parent / "sample_docs"


@pytest.fixture(scope="session", autouse=True)
def model():
    ensure_model()


@pytest.mark.parametrize("fname,expected", [("business_agreement.txt", "Business agreement"),
                                            ("court_order.txt", "Court paper"), ("pan_card.txt", "PAN card"),
                                            ("aadhaar_card.txt", "Aadhaar card")])
def test_classification(fname, expected):
    out = analyze_document(fname, (DOCS / fname).read_bytes())
    assert out["doc_type"] == expected


def test_pan_full_number():
    ents = ex.extract_entities("Permanent Account Number\nABCPR1234K\nName\nNEHA RASTOGI")
    assert {"type": "PAN number", "value": "ABCPR1234K"} in ents
    assert {"type": "Name", "value": "NEHA RASTOGI"} in ents


def test_pan_ocr_tolerant():
    assert ex.find_pans("AB0PR1234K") == ["ABOPR1234K"]


def test_aadhaar_full_number_and_vid():
    out = analyze_document("aadhaar_card.txt", (DOCS / "aadhaar_card.txt").read_bytes())
    assert out["doc_type"] == "Aadhaar card"
    c = out["id_card"]
    assert c["number"] == "2363 4521 8892" and c["name"] == "NEHA RASTOGI" and c["dob"] == "21/08/1998"
    assert c["vid"] == "9123 4567 8901 2345" and c["gender"] == "Female"


def test_verhoeff():
    assert ex.verhoeff_ok("2363") and not ex.verhoeff_ok("2364")


def test_contract_risk_and_clauses():
    out = analyze_document("c.txt", (DOCS / "business_agreement.txt").read_bytes())
    names = {c["name"] for c in out["clauses"]}
    assert {"Indemnity", "Non-compete", "Arbitration"} <= names
    assert out["risk"]["level"] in {"Medium", "High"}
    assert any(e["type"] == "Amount" for e in out["entities"])


def test_api_flow():
    with TestClient(app) as c:
        r = c.post("/api/auth/register", json={"name": "Test User", "email": "t@example.com", "password": "secret1"})
        if r.status_code == 409:
            r = c.post("/api/auth/login", json={"email": "t@example.com", "password": "secret1"})
        h = {"Authorization": "Bearer " + r.json()["access_token"]}
        assert c.post("/api/analyze", files={"file": ("a.txt", b"hello")}).status_code == 401
        up = c.post("/api/analyze", headers=h, files={"file": ("court_order.txt", (DOCS / "court_order.txt").read_bytes())})
        assert up.status_code == 200, up.text
        rid = up.json()["id"]
        pdf = c.get(f"/api/reports/{rid}/pdf", headers=h)
        assert pdf.content.startswith(b"%PDF")
        assert any(x["id"] == rid for x in c.get("/api/reports", headers=h).json())
        assert c.post("/api/analyze", headers=h, files={"file": ("x.exe", b"abc")}).status_code == 415


def test_other_document_is_not_forced_into_a_legal_type():
    out = analyze_document("recipe.txt", b"Recipe: Dal Tadka. Ingredients: lentils, onions, tomatoes, garlic. Heat oil in a pan and cook for 15 minutes. Serves 4 people.")
    assert out["doc_type"] == "Other document" and out["clauses"] == [] and "uncertain" in out
