from __future__ import annotations # ensure forward compatibility
import random, re, yaml # for parsing persona files
from pathlib import Path # for file path manipulations
from typing import Dict, Tuple # type hinting
from .store import SESSIONS # session management

PERSONA_DIR = Path(__file__).parent / "personas" # directory for persona files
_cache: Dict[str, Dict] = {} # in-memory cache for loaded personas

def load_persona(key: str) -> Dict:
    """
    Load a persona from a YAML file, using caching to avoid redundant loads.

    Args:
        key (str): The identifier for the persona file (without .yaml extension).

    Returns:
        Dict: The loaded persona data.
    """
    if key in _cache:
        return _cache[key]
    path = PERSONA_DIR / f"{key}.yaml"
    data = yaml.safe_load(path.read_text())
    _cache[key] = data
    return data

def choose_persona_auto(msg: str) -> str:
    """
    Automatically choose a persona based on keywords in the message.
    Args:
        msg (str): The input message to analyze.
    Returns:
        str: The chosen persona key.
    """

    msg_l = msg.lower() # lowercase for keyword matching
    if any(k in msg_l for k in ["budget", "cost", "margin", "ot", "finance"]):
        return "cfo"
    if any(k in msg_l for k in ["patient", "safety", "clinical", "icu", "ratio"]):
        return "physician"
    if any(k in msg_l for k in ["schedule", "shift", "staff", "overtime", "union", "ops"]):
        return "manager"
    return random.choice(["cfo", "physician", "manager"]) # fallback

def is_vague(question: str) -> bool:
    """
    Determine if a question is vague based on length and presence of vague words.

    Args:
        question (str): The question to evaluate.

    Returns:
        bool: True if the question is considered vague, False otherwise.
    """
    tokens = len(question.split()) # count words
    vague_words = ["stuff", "things", "etc", "idk", "whatever", "maybe"] # list of vague words
    return tokens < 5 or any(w in question.lower() for w in vague_words) # vague if short or contains vague words

def persona_reply(session_id: str, persona_key: str, message: str) -> Tuple[str, Dict]:
    """
    Generate a reply from a persona based on the input message, with rule-based disclosures.

    Args:
        session_id (str): The session identifier.
        persona_key (str): The persona identifier.
        message (str): The input message.
    Returns:
        Tuple[str, Dict]: The persona's reply and metadata (e.g., citations).
    """
    s = SESSIONS[session_id] # get session state
    p = load_persona(persona_key) # load persona data

    # patience
    if is_vague(message):
        s["patience"][persona_key] = max(0, s["patience"][persona_key] - 1) # decrease patience
    if s["patience"][persona_key] == 0: # if patience exhausted
        return (
        f"I need a focused, specific question to continue (e.g., ask about a numeric limit or policy).",
        {"citations": []},
    )

    # simple rule-based disclosure triggers
    text = message.lower() # lowercase for keyword matching
    cites = [] # list of citations to return

    # budget/cost → CFO
    if persona_key == "cfo" and any(k in text for k in ["budget", "cost", "ot", "margin"]): # keywords for CFO
        facts = [c for c in p["constraints"] if c.get("type") == "budget"] # find budget constraints
        if facts: # if any budget facts found
            cap = facts[0]["text"] # get budget text
            cites.append(facts[0].get("chunk_id", "")) # add citation
            return (
                f"Budget: {cap}. Margin target: "
                + next((o["text"] for o in p["objectives"] if "margin" in o["text"].lower()), "n/a"),
                {"citations": cites},
            )

    # staffing ratios → Physician
    if persona_key == "physician" and any(k in text for k in ["ratio", "safety", "error", "icu"]): # keywords for Physician
        fact = p["constraints"][0] # get first constraint
        cites.append(fact.get("chunk_id", "")) # add citation
        return (f"Clinical constraint: {fact['text']}", {"citations": cites})

    # scheduling/union → Manager
    if persona_key == "manager" and any(k in text for k in ["schedule", "shift", "union", "overtime"]): # keywords for Manager
        fact = p["constraints"][0] # get first constraint
        cites.append(fact.get("chunk_id", "")) # add citation
        return (f"Ops policy: {fact['text']}", {"citations": cites}) 

    # default concise reply with one objective and one constraint
    obj = p["objectives"][0]["text"] # get first objective
    cons = p["constraints"][0]["text"] # get first constraint
    cites.append(p["constraints"][0].get("chunk_id", "")) # add citation
    return (f"Goal: {obj}. Hard constraint: {cons}", {"citations": cites}) 

