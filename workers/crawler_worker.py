import io
import os
import time
from datetime import datetime

from bs4 import BeautifulSoup
from minio import Minio
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Account, Workflow
from app.services.workflow_engine import transition


def run_once():
    db: Session = SessionLocal()
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    client = Minio(
        endpoint,
        access_key=os.getenv("MINIO_ACCESS_KEY", "minio"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minio123"),
        secure=False,
    )
    bucket = os.getenv("MINIO_BUCKET", "raw-crawls")
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    for wf in db.query(Workflow).filter(Workflow.state == "DISCOVERED").all():
        account = db.query(Account).filter(Account.id == wf.account_id).first()
        if not account:
            continue
        html = f"<html><body><h1>{account.name}</h1><p>AI initiatives and cloud migration backlog with hiring push.</p></body></html>"
        object_name = f"{account.id}/{datetime.utcnow().isoformat()}.html"
        data = io.BytesIO(html.encode())
        client.put_object(bucket, object_name, data=data, length=len(html), content_type="text/html")
        soup = BeautifulSoup(html, "html.parser")
        wf.metadata_json = {
            "crawl_object": object_name,
            "text": soup.get_text(" ", strip=True),
            "source_url": f"https://{account.domain}",
            "crawled_at": datetime.utcnow().isoformat(),
        }
        wf.state = transition(wf.state, "CRAWLED")
    db.commit()
    db.close()


if __name__ == "__main__":
    while True:
        run_once()
        time.sleep(30)
