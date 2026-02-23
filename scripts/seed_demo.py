from app.database import Base, SessionLocal, engine
from app.models import Account, Contact, Workflow

Base.metadata.create_all(bind=engine)
db = SessionLocal()

accounts = [
    Account(name="Acme Fintech", domain="acmefintech.com", industry="fintech", geo="US", employee_range="100-500", revenue_range="$20M-$100M"),
    Account(name="Northstar Logistics", domain="northstarlogi.com", industry="logistics/supply-chain", geo="US", employee_range="500-2000", revenue_range="$100M-$500M"),
]
for a in accounts:
    db.merge(a)
db.commit()

acme = db.query(Account).filter(Account.domain == "acmefintech.com").first()
north = db.query(Account).filter(Account.domain == "northstarlogi.com").first()
contacts = [
    Contact(account_id=acme.id, name="Jane CTO", title="CTO", email="jane@acmefintech.com", persona="CTO"),
    Contact(account_id=north.id, name="Mark VP Eng", title="VP Engineering", email="mark@northstarlogi.com", persona="VP_ENG"),
]
for c in contacts:
    existing = db.query(Contact).filter(Contact.email == c.email).first()
    if not existing:
        db.add(c)
db.commit()

for c in db.query(Contact).all():
    if not db.query(Workflow).filter(Workflow.contact_id == c.id).first():
        db.add(Workflow(account_id=c.account_id, contact_id=c.id, state="DISCOVERED"))
db.commit()
print("Seed complete")
