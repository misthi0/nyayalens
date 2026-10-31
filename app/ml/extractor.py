"""Information extraction: entities, clauses, keywords, risk, summary.

Layers: (1) regex patterns for Indian legal/ID formats, (2) a clause library with risk weights,
(3) a legal-term lexicon for important words. Sensitive IDs are masked at extraction time.
"""
import re
from collections import Counter

DATE_RE = re.compile(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{4}\b", re.I)
AMOUNT_RE = re.compile(r"(?:Rs\.?|INR|₹)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:lakhs?|crores?))?", re.I)
VID_RE = re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)")
AADHAAR_RE = re.compile(r"(?<!\d)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\d)")
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
PAN_TOKEN = re.compile(r"\b[A-Z0-9]{10}\b")
PAN_4TH = set("PCHABGJLFT")  # 4th character = holder type
DOB_RE = re.compile(r"(?:DOB|D\.O\.B|Date of Birth|Year of Birth)\s*[:\-]?\s*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4})", re.I)
GENDER_RE = re.compile(r"\b(Male|Female|Transgender)\b", re.I)
LABEL2_RE = re.compile(r"(?im)^[ \t]*(name|father'?s name)[ \t]*\n[ \t]*([A-Z][A-Za-z .]{2,40}?)[ \t.]*$")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_RE = re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)")
CASE_RE = re.compile(r"\b(?:Case|Suit|Petition|C\.?S\.?)\s*No\.?\s*[\w/\-]+", re.I)
REG_RE = re.compile(r"Registration\s*No\.?\s*[\w/\-]+", re.I)
SECTION_RE = re.compile(r"\bSection\s+\d+[A-Z]?", re.I)
ORG_RE = re.compile(r"\b([A-Z][A-Za-z&]*(?:\s[A-Z][A-Za-z&]*)*\s(?:Pvt\.?\s?Ltd\.?|Private Limited|Limited|Ltd\.?|LLP|Traders|Enterprises|Industries|Associates))")
LABEL_RE = re.compile(r"\b((?i:name|plaintiff|defendant|petitioner|respondent|husband|wife|groom|bride|witness|father|deponent))(?:'s Name)?[ \t]*:[ \t]*([A-Z][a-zA-Z]+(?:[ \t][A-Z][a-zA-Z]+){0,3})")
LABEL_STOP = {"Next", "Date", "DOB", "Wife", "Husband", "Witness", "Defendant", "Plaintiff", "Case", "Registration",
              "Father", "Name", "Female", "Male", "Address", "Signature", "Permanent", "Income", "Petition", "Order", "Notary"}
LABEL_TYPE = {"name": "Name", "plaintiff": "Plaintiff", "defendant": "Defendant", "petitioner": "Petitioner",
              "respondent": "Respondent", "husband": "Husband", "wife": "Wife", "groom": "Groom", "bride": "Bride",
              "witness": "Witness", "father": "Father's name", "deponent": "Deponent"}

# clause name -> (regex, risk weight 1-3, plain-language explanation)
CLAUSES = {
    "Termination": (r"terminat", 1, "Check who can end the agreement, and how much notice is needed."),
    "Indemnity": (r"indemnif|indemnity|hold harmless", 3, "Indemnity shifts financial risk. You may have to cover the other side's losses."),
    "Penalty / liquidated damages": (r"penalt|liquidated damages|forfeit", 3, "A penalty applies on breach. Check the amount and when it triggers."),
    "Non-compete": (r"non[- ]?compete|restrain(?:t)? of trade|shall not (?:engage|carry on).{0,40}(?:business|competing)", 3, "Non-compete terms can limit your future work or business."),
    "Limitation of liability": (r"limitation of liability|shall not be liable|liability.{0,30}(?:limited|capped)", 3, "The other side may have capped what it owes you."),
    "Unilateral change": (r"(?:may|can|right to) (?:amend|modify|change|alter).{0,50}(?:at any time|sole discretion|without)", 3, "One side can change the terms without your consent."),
    "Auto-renewal": (r"auto[- ]?renew|automatically (?:renew|extend)|renew(?:s|ed)? automatically", 2, "The contract may continue unless you cancel in time."),
    "Arbitration": (r"arbitrat", 2, "Disputes go to arbitration rather than court. Check the seat and the rules."),
    "Exclusivity": (r"exclusiv", 2, "Exclusive terms can stop you from working with others."),
    "Late-payment interest": (r"interest (?:at|of|@)|late (?:fee|payment)", 2, "Delayed payments attract interest or fees."),
    "Confidentiality": (r"confidential|non[- ]disclosure", 1, "Information must be kept private. Check how long this lasts."),
    "Jurisdiction": (r"jurisdiction|governed by the laws", 1, "Sets which courts and laws apply."),
    "Force majeure": (r"force majeure|act of god", 1, "Covers events outside either party's control."),
    "Assignment": (r"assign(?:ment|s|ed)?\b", 1, "Check whether rights can be transferred to someone else."),
}
CLAUSE_TYPES = {"Business agreement", "Stamp paper", "Court paper"}

LEGAL_TERMS = ["agreement", "indemnity", "arbitration", "termination", "non-compete", "confidentiality", "penalty",
               "jurisdiction", "liability", "consideration", "warranty", "breach", "force majeure", "renewal",
               "notice", "governing law", "party", "witness", "affidavit", "notary", "stamp duty", "possession",
               "lease", "rent", "deposit", "plaintiff", "defendant", "petitioner", "respondent", "injunction", "damages",
               "hearing", "decree", "bail", "order", "petition", "judgment", "counsel", "appeal", "marriage", "husband",
               "wife", "registrar", "solemnized", "spouse", "aadhaar", "uidai", "permanent account number", "income tax",
               "date of birth", "attested", "deponent", "power of attorney", "sale deed", "gift deed", "exclusive",
               "assignment", "interest", "default", "waiver", "severability", "amendment"]
STOP = set("the of and to in a is that for on by with be as are this or at it from shall will any such which not may have has".split())


def _uniq(seq):
    seen, out = set(), []
    for t, v in seq:
        k = (t, v.lower())
        if k not in seen:
            seen.add(k)
            out.append({"type": t, "value": v})
    return out


_D = [[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],[3,4,0,1,2,8,9,5,6,7],[4,0,1,2,3,9,5,6,7,8],
      [5,9,8,7,6,0,4,3,2,1],[6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],[8,7,6,5,9,3,2,1,0,4],[9,8,7,6,5,4,3,2,1,0]]
_P = [[0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],[8,9,1,6,0,4,3,5,2,7],
      [9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],[2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]]
_TO_LETTER = {"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z", "6": "G"}
_TO_DIGIT = {"O": "0", "I": "1", "S": "5", "B": "8", "Z": "2", "G": "6"}


def verhoeff_ok(num: str) -> bool:
    """Aadhaar numbers carry a Verhoeff check digit, so a misread digit is detectable."""
    c = 0
    for i, ch in enumerate(reversed(num)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def find_aadhaar(text: str) -> list[tuple[str, bool]]:
    t = VID_RE.sub(" ", text)  # remove 16-digit VIDs so they are not read as an Aadhaar number
    out = []
    for m in AADHAAR_RE.finditer(t):
        raw = re.sub(r"\D", "", m.group(0))
        v = f"{raw[:4]} {raw[4:8]} {raw[8:]}"
        if v not in [o[0] for o in out]:
            out.append((v, verhoeff_ok(raw)))
    return out


def find_vid(text: str) -> list[str]:
    raw = dict.fromkeys(re.sub(r"\D", "", m.group(0)) for m in VID_RE.finditer(text))
    return [" ".join(v[i:i + 4] for i in range(0, 16, 4)) for v in raw]


def find_pans(text: str) -> list[str]:
    """Exact matches first, then OCR-tolerant matches (0/O, 1/I, 5/S, 8/B confusions fixed by position)."""
    found = [m.group(0) for m in PAN_RE.finditer(text)]
    for m in PAN_TOKEN.finditer(text):
        tok = m.group(0)
        fixed = "".join(_TO_LETTER.get(c, c) if i < 5 else _TO_DIGIT.get(c, c) if i < 9 else _TO_LETTER.get(c, c)
                        for i, c in enumerate(tok))
        if PAN_RE.fullmatch(fixed) and fixed[3] in PAN_4TH and fixed not in found:
            found.append(fixed)
    return found


def extract_entities(text: str) -> list[dict]:
    ents = []
    ents += [("Aadhaar number", v) for v, _ in find_aadhaar(text)]
    ents += [("VID", v) for v in find_vid(text)]
    ents += [("PAN number", v) for v in find_pans(text)]
    for m in LABEL_RE.finditer(text):
        toks = m.group(2).split()
        while toks and toks[-1] in LABEL_STOP:
            toks.pop()
        if toks:
            ents.append((LABEL_TYPE[m.group(1).lower()], " ".join(toks)))
    for m in LABEL2_RE.finditer(text):  # card layout: label on one line, value on the next
        t = "Father's name" if m.group(1).lower().startswith("father") else "Name"
        ents.append((t, m.group(2).strip()))
    dobs = [m.group(1) for m in DOB_RE.finditer(text)]
    ents += [("Date of birth", d) for d in dobs]
    ents += [("Gender", m.group(1).title()) for m in GENDER_RE.finditer(text)][:1]
    ents += [("Organisation", m.group(1).strip()) for m in ORG_RE.finditer(text)]
    ents += [("Date", m.group(0)) for m in DATE_RE.finditer(text) if m.group(0) not in dobs]
    ents += [("Amount", m.group(0).strip()) for m in AMOUNT_RE.finditer(text)]
    ents += [("Case number", re.sub(r"^.*?No\.?\s*", "", m.group(0), flags=re.I)) for m in CASE_RE.finditer(text)]
    ents += [("Registration number", re.sub(r"^.*?No\.?\s*", "", m.group(0), flags=re.I)) for m in REG_RE.finditer(text)]
    ents += [("Law section", m.group(0).title()) for m in SECTION_RE.finditer(text)]
    ents += [("Email", m.group(0)) for m in EMAIL_RE.finditer(text)]
    ents += [("Phone", re.sub(r"\D", "", m.group(0))[-10:]) for m in PHONE_RE.finditer(text)]
    return _uniq(ents)


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.;])\s+|\n{1,}", text)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def extract_clauses(text: str) -> list[dict]:
    sents, out = sentences(text), []
    for name, (rx, weight, why) in CLAUSES.items():
        pat = re.compile(rx, re.I)
        hit = next((s for s in sents if pat.search(s)), None)
        if hit:
            out.append({"name": name, "risk": weight, "explanation": why,
                        "snippet": hit if len(hit) <= 240 else hit[:237] + "..."})
    return sorted(out, key=lambda c: -c["risk"])


def keywords(text: str, n: int = 15) -> list[dict]:
    low = text.lower()
    found = [(t, len(re.findall(r"\b" + re.escape(t) + r"s?\b", low))) for t in LEGAL_TERMS]
    found = [(t, c) for t, c in found if c]
    if len(found) < 5:  # sparse text (e.g. ID cards): add frequent content words
        words = Counter(w for w in re.findall(r"[a-z]{4,}", low) if w not in STOP)
        found += [(w, c) for w, c in words.most_common(8) if w not in {t for t, _ in found}]
    return [{"term": t, "count": c} for t, c in sorted(found, key=lambda x: -x[1])[:n]]


def risk_score(clauses: list[dict]) -> dict:
    score = min(100, sum(c["risk"] for c in clauses) * 8)
    level = "High" if score >= 55 else "Medium" if score >= 25 else "Low"
    return {"score": score, "level": level}


def summarise(doc_type: str, text: str, ents: list[dict], clauses: list[dict]) -> str:
    kinds = Counter(e["type"] for e in ents)
    head = f"Detected as {doc_type.lower()}. Found {len(ents)} key details"
    if kinds:
        head += " (" + ", ".join(f"{c} {k.lower()}" for k, c in kinds.most_common(4)) + ")"
    head += f" and {len(clauses)} notable clauses." if clauses else "."
    if doc_type in {"Aadhaar card", "PAN card"}:
        return head + " ID details are shown in full below."
    scored = []
    for s in sentences(text)[:80]:
        sc = len(DATE_RE.findall(s)) + len(AMOUNT_RE.findall(s)) + len(ORG_RE.findall(s)) + (2 if re.search(r"agree|between|order|certif|affirm", s, re.I) else 0)
        scored.append((sc, s))
    top = [s for sc, s in sorted(scored, key=lambda x: -x[0])[:2] if sc]
    return head + (" Key lines: " + " ".join(x if len(x) < 220 else x[:217] + "..." for x in top) if top else "")
