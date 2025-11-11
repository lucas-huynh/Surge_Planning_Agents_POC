**Purpose:**  
This proof-of-concept (PoC) demonstrates an **interactive stakeholder interview simulator** for hospital surge planning.  
It combines a **FastAPI backend** (multi-persona logic) and a **Streamlit frontend** (UI + notes canvas) to help students explore how optimization, bandits, and dynamic programming problems are framed from conversations.

# ──────────────────────────────────────────────────────────────────────────────
# Repository layout
# ──────────────────────────────────────────────────────────────────────────────
# surge-poc/
# ├─ backend/
# │ ├─ app.py
# │ ├─ models.py
# │ ├─ persona_engine.py
# │ ├─ store.py
# │ └─ personas/
# │ ├─ cfo.yaml
# │ ├─ physician.yaml
# │ └─ manager.yaml
# ├─ frontend/
# │ └─ app.py
# ├─ requirements.txt
# └─ README.md
# ──────────────────────────────────────────────────────────────────────────────

---
## Quickstart
```bash
# 1) clone repo and cd surge-poc
python -m venv .venv && source .venv/bin/activate # on Windows: .venv\\Scripts\\activate
pip install -r requirements.txt


# 2) run backend (terminal A)
uvicorn backend.app:app --reload


# 3) run frontend (terminal B)
streamlit run frontend/app.py
```

Open the Streamlit URL it prints (usually http://localhost:8501). Start a session from the sidebar, pick @mention=auto (or a specific persona), and ask a focused question. Click **Pin** to push the last persona answer into the right‑hand canvas.


## What’s implemented (MVP)
- FastAPI endpoints: `/session`, `/personas`, `/chat`, `/pin`, `/notes`.
- In‑memory sessions with a 7‑minute time limit and persona‑specific patience.
- Three authorable personas in YAML (CFO, Physician, Manager) with objectives, constraints, and simple disclosure rules.
- Streamlit UI with @mentions, live Notes canvas, and one‑click Pin.

## Functional Test
1) Persona loading
Click Persona cards expander → confirm you see:
@cfo, @physician, @manager with role/name/temperament.

2) Auto-routing (@mention = auto)
Try these one-liners (auto should route by keyword):

Budget: “How does OT spending affect margin this month?” → routes to CFO and mentions OT cap/margin.

Ratios: “What is the safe ICU nurse ratio during a surge?” → routes to Physician, returns ratio constraint.

Scheduling: “Can we add a double shift to cover Friday night?” → routes to Manager, returns union/double-shift rule.

3) Direct routing (@mention specific)
Set @mention to each persona and ask:

@cfo: “What’s the current overtime budget cap?” → expects $180,000/month.

@physician: “What patient-to-nurse ratios are acceptable on surge unit?”

@manager: “What limits do union rules place on weekly shifts?”

4) “Pin to Notes” workflow
After a good answer:

In sidebar, set Bucket = constraints → click Pin.

Expand Notes (live) → under Constraints you should see the pinned text.

Repeat with another answer; change Bucket to states or actions and pin again.

Confirm the correct tab on the right shows those bullets.

5) Patience / vague-question mechanics
Set @mention = cfo and send a few intentionally vague prompts:

thoughts?
can you elaborate more on stuff?
idk maybe budget?


You should see patience decrement. When it hits 0, reply becomes:

“I need a focused, specific question to continue (e.g., ask about a numeric limit or policy).”
You can restore patience by starting a new session.

6) Default fallback (no trigger keywords)
Ask each persona something neutral:
“What is your main goal for surge planning?”
Expect the generic:

“Goal: … Hard constraint: …” (from the first objective/constraint in YAML).