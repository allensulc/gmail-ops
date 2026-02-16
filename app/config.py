import os

def must(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

GOOGLE_CLIENT_ID = must("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = must("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = must("GOOGLE_REFRESH_TOKEN")

# Full Pub/Sub topic name, e.g.:
# projects/<PROJECT_ID>/topics/<TOPIC_NAME>
GMAIL_PUBSUB_TOPIC = must("GMAIL_PUBSUB_TOPIC")

# Used to verify Pub/Sub push requests (we set it as a query param on the push endpoint)
WEBHOOK_SECRET = must("WEBHOOK_SECRET")

DATABASE_URL = must("DATABASE_URL")

# Label namespace
LABEL_PREFIX = os.getenv("LABEL_PREFIX", "OPS/")
