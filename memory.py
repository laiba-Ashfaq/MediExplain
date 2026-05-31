"""
MediExplain — Session Memory
Logs queries and responses to session_history.csv.
"""

import csv
import uuid
import json
from datetime import datetime
from pathlib import Path

HISTORY_PATH = Path(__file__).parent / "data" / "session_history.csv"
FIELDNAMES = ["session_id", "timestamp", "user_query", "extracted_tests", "llm_response", "model_used", "prompt_strategy"]


def log_session(user_query: str, extracted_tests: list, llm_response: str,
                model_used: str = "demo", prompt_strategy: str = "One-Shot+CoT+FewKnowledge",
                session_id: str = None) -> str:
    """Append a session record to history CSV. Returns the session_id."""
    sid = session_id or str(uuid.uuid4())[:8]
    row = {
        "session_id": sid,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user_query": user_query[:500],
        "extracted_tests": json.dumps([t.get("test_name", "") for t in extracted_tests]),
        "llm_response": llm_response[:1000],
        "model_used": model_used,
        "prompt_strategy": prompt_strategy,
    }
    write_header = not HISTORY_PATH.exists() or HISTORY_PATH.stat().st_size == 0
    with open(HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return sid


def get_history(limit: int = 10) -> list[dict]:
    """Return last `limit` session records."""
    if not HISTORY_PATH.exists():
        return []
    with open(HISTORY_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-limit:]
