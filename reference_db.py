"""
MediExplain — Reference Database Toolkit
Looks up normal ranges from reference_ranges.csv.
"""
import csv
import os

_DB = []
_LOADED = False

def _load():
    global _DB, _LOADED
    if _LOADED:
        return
    path = os.path.join(os.path.dirname(__file__), "data", "reference_ranges.csv")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["low_normal"] = float(row["low_normal"]) if row["low_normal"] else None
            row["high_normal"] = float(row["high_normal"]) if row["high_normal"] else None
            _DB.append(row)
    _LOADED = True


def lookup(test_name: str, sex: str = "both") -> dict | None:
    """
    Return the best-matching reference range row for a test name and sex.
    sex: 'male', 'female', or 'both'
    """
    _load()
    test_lower = test_name.lower().strip()
    candidates = []

    for row in _DB:
        # match canonical name
        if row["test_name"].lower() == test_lower:
            candidates.append(row)
            continue
        # match any alias
        aliases = [a.lower() for a in row["aliases"].split("|")]
        if test_lower in aliases:
            candidates.append(row)

    if not candidates:
        return None

    # prefer sex-specific rows
    for row in candidates:
        if row["sex"].lower() == sex.lower():
            return row
    # fallback to "both"
    for row in candidates:
        if row["sex"].lower() == "both":
            return row
    return candidates[0]
