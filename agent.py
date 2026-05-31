"""
MediExplain — Core Agent (Groq + LLaMA 3.3 Version)
Orchestrates the Brain (LLM), Memory (CSV), and Toolkit (parser + reference DB).
"""
import os
import csv
import uuid
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

from parser import parse_query
from reference_db import lookup

# ── Session memory ───────────────────────────────────────────────────────────
SESSION_CSV = os.path.join(os.path.dirname(__file__), "data", "session_history.csv")

# ── Load prompt files ────────────────────────────────────────────────────────
_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def _read(fname):
    with open(os.path.join(_PROMPTS_DIR, fname), encoding="utf-8") as f:
        return f.read()

SYSTEM_PROMPT = _read("system_prompt.txt")
ONE_SHOT      = _read("one_shot_example.txt")

# ── Session logger ───────────────────────────────────────────────────────────
def _log_session(session_id, query, response, model):
    with open(SESSION_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            session_id,
            datetime.utcnow().isoformat(),
            query.replace("\n", " "),
            response.replace("\n", " ")[:500],
            model
        ])

# ── Status classifier ────────────────────────────────────────────────────────
def classify_status(value, low, high):
    if low is None or high is None:
        return "UNKNOWN"
    if value < low:
        ratio = (low - value) / low if low != 0 else 1
        return "CRITICALLY LOW" if ratio > 0.3 else "LOW"
    if value > high:
        ratio = (value - high) / high if high != 0 else 1
        return "CRITICALLY HIGH" if ratio > 0.5 else "HIGH"
    return "NORMAL"

STATUS_EMOJI = {
    "NORMAL":          "🟢",
    "LOW":             "🟡",
    "HIGH":            "🟡",
    "CRITICALLY LOW":  "🔴",
    "CRITICALLY HIGH": "🔴",
    "UNKNOWN":         "⚪",
}

# ── Build structured prompt ──────────────────────────────────────────────────
def build_user_message(parsed_tests, sex="both"):
    lines   = []
    summary = []

    for t in parsed_tests:
        ref_row = lookup(t["test_name"], sex)

        low  = t["user_ref_low"]  if t["user_ref_low"]  is not None else (ref_row["low_normal"]  if ref_row else None)
        high = t["user_ref_high"] if t["user_ref_high"] is not None else (ref_row["high_normal"] if ref_row else None)
        unit = t["unit"] or (ref_row["unit"] if ref_row else "")

        status = classify_status(t["value"], low, high)
        emoji  = STATUS_EMOJI[status]
        ref_str = f"{low} – {high} {unit}".strip() if (low is not None and high is not None) else "Not found in database"

        lines.append(
            f"Test: {t['test_name']} | "
            f"Value: {t['value']} {unit} | "
            f"Reference Range: {ref_str} | "
            f"Status: {emoji} {status}"
        )
        summary.append({
            "test_name": t["test_name"],
            "value":     t["value"],
            "status":    status
        })

    if not lines:
        return None, []

    user_msg = (
        "Please explain the following laboratory test result(s) to the patient "
        "using the Chain-of-Thought approach: first identify the test and its normal range, "
        "then classify the value, then explain what it means in plain language, "
        "then list possible reasons, then give a recommendation.\n\n"
        + "\n".join(lines)
    )
    return user_msg, summary


# ── Main agent call ──────────────────────────────────────────────────────────
def run_agent(user_query, sex="both", model="llama-3.3-70b-versatile", session_id=None):
    """
    Full pipeline:
      1. Parse query  →  2. Reference DB lookup  →  3. Build prompt
      →  4. Call Groq (LLaMA 3.3)  →  5. Log session  →  6. Return result dict
    """
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    # Step 1 & 2: Toolkit — parse + reference lookup
    parsed = parse_query(user_query)

    if not parsed:
        return {
            "session_id": session_id,
            "success":    False,
            "message": (
                "I couldn't detect any lab values in your message. "
                "Please include the test name and value, e.g.: "
                '"My Hemoglobin is 10.2 g/dL" or "HbA1c = 8.1%"'
            ),
            "tests":    [],
            "markdown": "",
        }

    # Step 2: Build structured prompt
    user_msg, test_summary = build_user_message(parsed, sex)

    if not user_msg:
        return {
            "session_id": session_id,
            "success":    False,
            "message":    "Could not parse values.",
            "tests":      [],
            "markdown":   ""
        }

    # Step 3: Brain — One-Shot + CoT + Few Knowledge combined prompt
    full_prompt = f"""{SYSTEM_PROMPT}

--- ONE-SHOT EXAMPLE (follow this format exactly) ---
{ONE_SHOT}
--- END EXAMPLE ---

Now apply the same format to the following patient results:

{user_msg}
"""

    # Check API key
    if not os.environ.get("GROQ_API_KEY"):
        return {
            "session_id": session_id,
            "success":    False,
            "message":    "Groq API key not set. Please add GROQ_API_KEY to your .env file.",
            "tests":      test_summary,
            "markdown":   "",
        }

    # Step 4: Groq LLM call (LLaMA 3.3 70B) ← fixed model name here
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",        # ← FIXED
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": full_prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        answer = response.choices[0].message.content

    except Exception as e:
        return {
            "session_id": session_id,
            "success":    False,
            "message":    f"LLM error: {str(e)}",
            "tests":      test_summary,
            "markdown":   "",
        }

    # Step 5: Log to memory (session_history.csv)
    _log_session(session_id, user_query, answer, "llama-3.3-70b-versatile")

    return {
        "session_id": session_id,
        "success":    True,
        "message":    "OK",
        "tests":      test_summary,
        "markdown":   answer,
    }