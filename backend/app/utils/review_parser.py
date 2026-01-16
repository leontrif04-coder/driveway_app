# backend/app/utils/review_parser.py
from typing import List, Literal

MeterStatus = Literal["working", "broken", "unknown"]

BROKEN_KEYWORDS = [
    "broken",
    "doesn't work",
    "doesnt work",
    "not working",
    "ate my coins",
    "out of order",
    "error",
    "malfunction",
]
WORKING_KEYWORDS = ["works", "working fine", "no issues", "all good"]

def parse_meter_status(reviews: List[str]) -> tuple[MeterStatus, float]:
    broken = 0
    working = 0
    for txt in reviews:
        t = txt.lower()
        if any(kw in t for kw in BROKEN_KEYWORDS):
            broken += 1
        if any(kw in t for kw in WORKING_KEYWORDS):
            working += 1

    total = broken + working
    if total == 0:
        return "unknown", 0.0
    if broken > working:
        return "broken", broken / total
    return "working", working / total


