from typing import Dict
from .config import LABEL_PREFIX

OPS_LABELS = [
    "IMPORTANT",
    "WATCHLIST",
    "ACTION_REQUIRED",
    "TIME_SENSITIVE",
    "WORK",
    "SCHOOL",
    "FINANCE",
    "LOGISTICS",
    "REFERENCE",
    "NEWSLETTERS",
    "PROMOS",
    "SOCIAL",
]

def ensure_labels(service) -> Dict[str, str]:
    """
    Ensure OPS labels exist. Returns mapping label_name -> label_id.
    """
    existing = service.users().labels().list(userId="me").execute().get("labels", [])
    by_name = {l["name"]: l["id"] for l in existing}

    out: Dict[str, str] = {}
    for short in OPS_LABELS:
        name = f"{LABEL_PREFIX}{short}"
        if name not in by_name:
            created = service.users().labels().create(
                userId="me",
                body={
                    "name": name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            ).execute()
            by_name[name] = created["id"]
        out[name] = by_name[name]
    return out

def apply_labels(service, message_id: str, label_ids: list[str]) -> None:
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": label_ids, "removeLabelIds": []},
    ).execute()
