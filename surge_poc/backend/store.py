from __future__ import annotations # ensure forward-reference compatibility
import time # time tracking for sessions
from typing import Dict, Any # expected data types for store
from uuid import uuid4 # unique session IDs

# in-memory store of all user sessions (simple for PoC), can be replaced with persistent DB later
SESSIONS: Dict[str, Any] = {}

DEFAULT_TIME_LIMIT_S = 7 * 60 # 7 minutes

BUCKETS = [
"states", "actions", "transitions", "rewards",
"constraints", "uncertainties", "tradeoffs"
]

def new_session(seed: int) -> str:
    """
    Create a new interactive session for the Hospital Surge Staffing tool.

    Initializes an in-memory session object containing metadata
    for a student's stakeholder meeting, including the random seed for deterministic
    persona behavior, session start time, time limit, persona patience counters,
    and empty notes buckets.

    Args:
        seed (int): Random seed used to control reproducibility of persona behavior.

    Returns:
        str: A unique 12-character session ID (hex string) that identifies the session
             and can be used in subsequent API calls (e.g., /chat, /pin, /notes).
    """
    sid = uuid4().hex[:12]
    SESSIONS[sid] = {
        "seed": seed,
        "started_at": time.time(),
        "time_limit_s": DEFAULT_TIME_LIMIT_S,
        "patience": {"cfo": 5, "physician": 6, "manager": 6},
        "last_reply": "",
        "notes": {b: [] for b in BUCKETS},
        }
    return sid

def time_left(session_id: str) -> int:
    """
    Calculate the remaining time (in seconds) for a given session.

    Args:
        session_id (str): Unique identifier of the active session.

    Returns:
        int: Number of seconds remaining before the session times out.
             Returns 0 if the time limit has been reached.
    """
    s = SESSIONS[session_id]
    elapsed = int(time.time() - s["started_at"])
    return max(0, s["time_limit_s"] - elapsed)