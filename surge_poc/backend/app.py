from __future__ import annotations # ensure forward compatibility
from fastapi import FastAPI, HTTPException # web framework and error handling
from fastapi.middleware.cors import CORSMiddleware # CORS middleware
from .models import * # data models
from .store import new_session, time_left, SESSIONS # session management
from .persona_engine import choose_persona_auto, persona_reply, load_persona # persona logic

app = FastAPI(title="Surge-Staffing PoC API") # initialize FastAPI app
app.add_middleware( # add CORS middleware
    CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/session", response_model=StartSessionResponse) # start a new session
def start_session(req: StartSessionRequest):
    """
    Start a new session with an optional seed for reproducibility.
    Args:
        req (StartSessionRequest): The request containing an optional seed.
    Returns:
        StartSessionResponse: The response containing the new session ID.
    """
    sid = new_session(req.seed)
    return StartSessionResponse(session_id=sid, seed=req.seed)

@app.get("/personas", response_model=PersonasResponse) # list available personas
def list_personas():
    """
    List all available personas with their details.
    Returns:
        PersonasResponse: The response containing all persona details.
    """
    data = {}
    for key in ["cfo", "physician", "manager"]:
        p = load_persona(key)
        data[key] = PersonaCard(
        role=p["identity"]["role"],
        name=p["identity"]["name"],
        temperament=p["identity"]["temperament"],
        style=p["style"],
        objectives=p["objectives"],
        constraints=p["constraints"],
    )
    return PersonasResponse(personas=data)

@app.post("/chat", response_model=ChatResponse) # chat endpoint
def chat(req: ChatRequest):
    """
    Handle a chat message, selecting persona and generating a reply.

    Args:
        req (ChatRequest): The chat request containing session ID, persona, and message.

    Returns:
        ChatResponse: The response containing the reply and metadata.
    """
    if req.session_id not in SESSIONS: # validate session
        raise HTTPException(404, "Unknown session")
    persona = req.persona.lower() # get persona
    if persona == "auto": 
        persona = choose_persona_auto(req.message)
    reply, meta = persona_reply(req.session_id, persona, req.message)
    SESSIONS[req.session_id]["last_reply"] = reply
    return ChatResponse(
        reply=reply,
        persona=persona,
        citations=meta.get("citations", []),
        time_left_s=time_left(req.session_id),
        patience_left=SESSIONS[req.session_id]["patience"][persona],
    )

@app.post("/pin", response_model=NotesResponse)
def pin(req: PinRequest): 
    """
    Pin a note with citations to the session's notes under the specified bucket.

    Args:
        req (PinRequest): The pin request containing session ID, bucket, text, and citations

    Returns:
        NotesResponse: The updated notes for the session.
    """
    s = SESSIONS.get(req.session_id)
    if not s:
        raise HTTPException(404, "Unknown session")
    s["notes"][req.bucket].append({"text": req.text, "citations": req.citations})
    return NotesResponse(notes=s["notes"])

@app.get("/notes", response_model=NotesResponse)
def get_notes(session_id: str):
    """
    Retrieve the notes for the specified session.
    Args:
        session_id (str): The session identifier.
    
    Returns:
        NotesResponse: The notes for the session.
    """
    s = SESSIONS.get(session_id)
    if not s:
        raise HTTPException(404, "Unknown session")
    return NotesResponse(notes=s["notes"])

