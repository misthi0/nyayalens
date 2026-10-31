"""Synthetic starter corpus (so the project runs out of the box).
Replace with real, labelled documents for production: put them in a CSV with columns text,label."""
import random

FIRST = "Rahul Amit Priya Neha Suresh Anil Mohan Ravi Pooja Kavita Vikram Sunita Arjun Deepak Meena Rohit".split()
LAST = "Sharma Verma Gupta Singh Rastogi Tyagi Kumar Agarwal Mishra Yadav Jain Chauhan Saini".split()
CITY = ["Meerut", "Lucknow", "Delhi", "Pune", "Jaipur", "Kanpur", "Noida", "Mumbai", "Bhopal"]
ORGS = ["Verma Pvt Ltd", "Sharma Traders", "Gupta Industries", "Singh Associates", "Kumar LLP", "Mishra Enterprises", "Jain Private Limited"]
ACTS = ["Hindu Marriage Act", "Special Marriage Act", "Indian Contract Act", "Code of Civil Procedure", "Indian Penal Code"]

n = lambda r: f"{r.choice(FIRST)} {r.choice(LAST)}"
date = lambda r: f"{r.randint(1, 28):02d}/{r.randint(1, 12):02d}/{r.randint(2012, 2026)}"
amt = lambda r: "Rs. " + f"{r.randint(1, 99) * r.choice([1000, 5000, 10000, 50000]):,}"
pan = lambda r: "".join(r.choice("ABCDEFGHJKLMNPRSTVWXYZ") for _ in range(5)) + f"{r.randint(1000, 9999)}" + r.choice("ABCDEFGHK")
digits = lambda r, k: "".join(str(r.randint(0, 9)) for _ in range(k))

BIZ = ["Either party may terminate this agreement with {d} days written notice.", "The parties shall keep all information strictly confidential.",
       "The first party shall indemnify the second party against all losses and claims.", "Any dispute shall be resolved by arbitration in {c}.",
       "A penalty of {a} shall be payable on breach of this agreement.", "The agreement renews automatically unless cancelled.",
       "The courts at {c} shall have exclusive jurisdiction.", "The second party shall not engage in any competing business for two years (non-compete).",
       "Neither party is liable for delay caused by force majeure events.", "Payment is due within 30 days; late payment attracts interest at 18% per annum.",
       "The consideration is payable in three instalments.", "Liability of the supplier is limited to the fees paid."]
COURT = ["The matter is listed for hearing on {dt}.", "The court issues notice to the respondent.", "Interim injunction is granted till the next date.",
         "Damages of {a} are awarded to the plaintiff.", "The bail application is dismissed.", "Counsel for the petitioner submitted arguments.",
         "The written statement shall be filed within four weeks.", "Judgment is reserved.", "The appeal is admitted and the decree is stayed."]
STAMP = ["The deponent solemnly affirms that the contents are true.", "Possession of the property is handed over today.", "This deed is attested by the Notary Public.",
         "The monthly rent is {a} with a security deposit.", "The executant declares full ownership of the property.", "Stamp duty has been paid as per the Indian Stamp Act.",
         "The power of attorney is irrevocable.", "The donor gifts the property out of natural love and affection."]


def business(r):
    kind = r.choice(["Service", "Supply", "Partnership", "Consultancy", "Lease", "Employment"])
    head = f"This {kind} Agreement is made on {date(r)} between {r.choice(ORGS)} (the First Party) and {r.choice(ORGS)} (the Second Party). The consideration is {amt(r)}. The term is {r.randint(6, 36)} months."
    body = " ".join(s.format(d=r.choice([15, 30, 60]), c=r.choice(CITY), a=amt(r)) for s in r.sample(BIZ, r.randint(3, 6)))
    return f"{head} {body} IN WITNESS WHEREOF the parties have signed."


def court(r):
    head = (f"IN THE COURT OF {r.choice(['DISTRICT JUDGE', 'CIVIL JUDGE', 'SESSIONS JUDGE', 'HIGH COURT'])}, {r.choice(CITY)}. Case No. {r.randint(1, 999)}/{r.randint(2015, 2026)}. "
            f"Plaintiff: {n(r)}. Defendant: {n(r)}. Petition under Section {r.randint(10, 498)} of the {r.choice(ACTS)}.")
    return head + " " + " ".join(s.format(dt=date(r), a=amt(r)) for s in r.sample(COURT, r.randint(3, 5)))


def marriage(r):
    t = r.choice(["Certificate of Marriage", "Marriage Registration Certificate", "Vivah Praman Patra"])
    return (f"{t}. This is to certify that the marriage between Husband: {n(r)} and Wife: {n(r)} was solemnized on {date(r)} at {r.choice(CITY)} "
            f"under the {r.choice(ACTS[:2])}. Registration No. MR/{r.randint(2010, 2026)}/{r.randint(100, 9999)}. Witness: {n(r)}. Marriage Registrar.")


def stamp(r):
    kind = r.choice(["Affidavit", "Rent Agreement", "Sale Deed", "Power of Attorney", "Gift Deed"])
    return (f"Non judicial stamp paper of {amt(r)}. {kind} executed on {date(r)} by {n(r)}, resident of {r.choice(CITY)}. "
            + " ".join(s.format(a=amt(r)) for s in r.sample(STAMP, r.randint(3, 5))) + " Notary Public attested.")


def aadhaar(r):
    return (f"Government of India Unique Identification Authority of India Aadhaar Name: {n(r)} DOB: {date(r)} {r.choice(['Male', 'Female'])} "
            f"{digits(r, 4)} {digits(r, 4)} {digits(r, 4)} VID: {digits(r, 16)} Mera Aadhaar Meri Pehchaan Address: {r.choice(CITY)}")


def pan_card(r):
    return (f"INCOME TAX DEPARTMENT GOVT. OF INDIA Permanent Account Number {pan(r)} Name: {n(r).upper()} Father's Name: {n(r).upper()} "
            f"Date of Birth: {date(r)} Signature")


FOOD = "paneer rice onions tomatoes garlic ginger lentils butter cumin coriander flour milk sugar chillies potatoes spinach".split()


def recipe(r):
    return (f"Recipe: {r.choice(['Paneer Curry', 'Veg Pulao', 'Dal Tadka', 'Aloo Paratha', 'Masala Chai'])}. Ingredients: {', '.join(r.sample(FOOD, 5))}. "
            f"Heat oil in a pan, add the spices and cook for {r.randint(5, 20)} minutes. Serve hot. Serves {r.randint(2, 6)} people.")


def resume(r):
    return (f"{n(r)} Resume. Email: {r.choice(FIRST).lower()}@example.com. Objective: seeking a role in software development. "
            f"Skills: Python, SQL, machine learning, communication. Education: B.Tech in Computer Science, {r.randint(2018, 2025)}. "
            f"Projects: chatbot, sales dashboard. Experience: intern at a startup for {r.randint(2, 12)} months.")


def news(r):
    return (f"{r.choice(CITY)}: The city saw heavy rain on {r.choice(['Monday', 'Tuesday', 'Friday'])} as temperatures dropped to {r.randint(15, 28)} degrees. "
            f"Officials said traffic was affected on several roads and schools reopened the next day. The cricket team won by {r.randint(2, 90)} runs in the final.")


def invoice(r):
    return (f"Invoice No. {r.randint(1000, 9999)} dated {date(r)}. Bill to: {n(r)}. Item: {r.choice(['laptop bag', 'notebook', 'phone charger', 'headphones'])} "
            f"quantity {r.randint(1, 5)} price {amt(r)}. GST 18 percent. Total amount {amt(r)}. Thank you for shopping with us.")


def lecture(r):
    return (f"Lecture notes week {r.randint(1, 12)}: {r.choice(['Photosynthesis', 'Newton laws of motion', 'Linear regression', 'The French Revolution', 'Database normalisation'])}. "
            f"Key points: definition, examples, diagram, exercises. Homework: solve questions {r.randint(1, 5)} to {r.randint(6, 15)} from the textbook. Quiz on {date(r)}.")


def chat(r):
    return (f"Hi {r.choice(FIRST)}, are we still meeting at {r.randint(1, 11)} pm on Saturday? I will bring the notes and some snacks. "
            f"Let me know if the plan changes. Also did you watch the match yesterday? It was amazing. See you soon, {r.choice(FIRST)}.")


def travel(r):
    return (f"Booking confirmation. Flight from {r.choice(CITY)} to {r.choice(CITY)} on {date(r)}. Passenger {n(r)}. Seat {r.randint(1, 30)}{r.choice('ABCDEF')}. "
            f"Boarding at {r.randint(5, 22)}:{r.choice(['00', '15', '30', '45'])}. Please arrive two hours early. Fare {amt(r)}.")


def prescription(r):
    return (f"Clinic visit {date(r)}. Patient {n(r)}, age {r.randint(18, 70)}. Symptoms: fever and cough for {r.randint(2, 6)} days. "
            f"Advice: rest, drink fluids. Tablets twice a day after meals for {r.randint(3, 7)} days. Follow up if symptoms continue.")


OTHERS = [recipe, resume, news, invoice, lecture, chat, travel, prescription]


def other(r):
    return r.choice(OTHERS)(r)


SWAP = {"O": "0", "0": "O", "l": "1", "1": "l", "I": "l", "S": "5", "B": "8", "e": "c", "a": "o"}


def _typo(r, w):
    if len(w) < 3:
        return w
    k, i = r.random(), r.randrange(len(w))
    if k < 0.35:
        return w[:i] + w[i + 1:]  # dropped letter
    if k < 0.7 and w[i] in SWAP:
        return w[:i] + SWAP[w[i]] + w[i + 1:]  # OCR confusion (O/0, l/1 ...)
    if i < len(w) - 1:
        return w[:i] + w[i + 1] + w[i] + w[i + 2:]  # swapped letters
    return w


def noisy(r, text, level=None):
    """Mimic scan / OCR damage: dropped words, letter swaps, broken lines. level 0 = clean text."""
    level = r.choice([0, 0, 0.03, 0.06, 0.12]) if level is None else level
    if not level:
        return text
    out = []
    for w in text.split():
        x = r.random()
        if x < level * 0.5:
            continue
        if x < level * 1.5:
            w = _typo(r, w)
        out.append(w)
        if r.random() < level * 0.4:
            out.append("\n")
    return " ".join(out)


MAKERS = {"Business agreement": business, "Court paper": court, "Marriage certificate": marriage,
          "Stamp paper": stamp, "Aadhaar card": aadhaar, "PAN card": pan_card, "Other document": other}


def _noise(r, text, p=0.04):
    return " ".join(w for w in text.split() if r.random() > p)  # mimic OCR drop-outs


def generate(per_class=150, seed=7):
    r = random.Random(seed)
    texts, labels = [], []
    for label, fn in MAKERS.items():
        for _ in range(per_class):
            texts.append(noisy(r, fn(r)))
            labels.append(label)
    return texts, labels
