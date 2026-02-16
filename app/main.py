import base64
import json
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import text

from .db import engine, init_db
from .gmail_client import gmail_service
from .labels import ensure_labels, apply_labels
from .classify import classify
from .config import WEBHOOK_SECRET, GMAIL_PUBSUB_TOPIC, LABEL_PREFIX

app = FastAPI()

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}
    
@app.get("/")
def root():
    return {"ok": True}
    
@app.post("/gmail/push")
async def gmail_push(request: Request, secret: str):
    # Simple shared-secret check to prevent random internet hits
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="bad secret")

    body = await request.json()
    msg = body.get("message", {})
    data_b64 = msg.get("data")
    if not data_b64:
        return {"ok": True, "note": "no data"}

    payload = json.loads(base64.b64decode(data_b64).decode("utf-8"))
    # payload typically contains emailAddress + historyId
    history_id = payload.get("historyId")
    if not history_id:
        return {"ok": True, "note": "no historyId"}

    service = gmail_service()

    # Get history since historyId: we use the historyId from push as "startHistoryId".
    # This may miss items if you haven't set an initial startHistoryId properly.
    # We'll fix that by calling /admin/watch once the topic/subscription are set.
    hist = service.users().history().list(
        userId="me",
        startHistoryId=history_id,
        historyTypes=["messageAdded"],
    ).execute()

    histories = hist.get("history", [])
    message_ids = []
    for h in histories:
        for m in h.get("messagesAdded", []):
            mid = m.get("message", {}).get("id")
            if mid:
                message_ids.append(mid)

    # Process messages
    labels_map = ensure_labels(service)
    for mid in set(message_ids):
        # idempotency: skip if processed
        with engine.begin() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM processed_messages WHERE message_id=:mid"),
                {"mid": mid},
            ).first()
            if exists:
                continue

        m = service.users().messages().get(
            userId="me",
            id=mid,
            format="metadata",
            metadataHeaders=["From", "Subject"],
        ).execute()

        headers = {h["name"].lower(): h["value"] for h in m.get("payload", {}).get("headers", [])}
        from_h = headers.get("from", "")
        subject = headers.get("subject", "")
        snippet = m.get("snippet", "")

        cls = classify(subject=subject, snippet=snippet, from_header=from_h)

        primary_label = f"{LABEL_PREFIX}{cls.label_short}"
        label_ids = [labels_map[primary_label]]

        # Also add IMPORTANT if very high
        if cls.priority >= 85:
            label_ids.append(labels_map[f"{LABEL_PREFIX}IMPORTANT"])

        apply_labels(service, mid, label_ids)

        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO processed_messages(message_id, label_applied, priority, category)
                    VALUES (:mid, :lab, :pri, :cat)
                """),
                {"mid": mid, "lab": primary_label, "pri": cls.priority, "cat": cls.category},
            )

    return {"ok": True, "processed": len(set(message_ids))}

@app.post("/admin/watch")
def admin_watch():
    """
    Call this once AFTER you have:
    - Pub/Sub topic created
    - Push subscription pointing to Railway /gmail/push?secret=...
    - Granted gmail-api-push@system.gserviceaccount.com Pub/Sub Publisher on topic
    """
    service = gmail_service()
    resp = service.users().watch(
        userId="me",
        body={
            "topicName": GMAIL_PUBSUB_TOPIC,
            # Optional: only watch INBOX
            "labelIds": ["INBOX"],
        },
    ).execute()
    return {"ok": True, "watch": resp}
