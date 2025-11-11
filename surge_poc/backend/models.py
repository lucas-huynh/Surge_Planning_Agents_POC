from __future__ import annotations # ensure forward-reference compatibility 
from pydantic import BaseModel, Field # Pydantic core class
from typing import List, Dict, Optional # expected data types for attributes

class StartSessionRequest(BaseModel): # request to start session
    seed: int = 42

class StartSessionResponse(BaseModel): # API returns random session ID and seed for reproducibility
    session_id: str
    seed: int

class ChatRequest(BaseModel): # frontend sends session, persona, and message
    session_id: str
    persona: str # "cfo", "physician", "manager", "auto"
    message: str

class ChatResponse(BaseModel): # backend responds with reply, persona, citations, time left, patience left
    reply: str
    persona: str
    citations: List[str] = []
    time_left_s: int
    patience_left: int

class PinRequest(BaseModel): # tells backend which category to pin snippet in
    session_id: str
    bucket: str # states, actions, transitions, rewards, constraints, uncertainties, tradeoffs
    text: str
    citations: List[str] = []

class NotesResponse(BaseModel): # returns all pinned snippets organized by category
    notes: Dict[str, List[Dict]]

class PersonaCard(BaseModel): # each persona's attributes
    role: str
    name: str
    temperament: str
    style: Dict[str, Any]
    objectives: List[Dict]
    constraints: List[Dict]

class PersonasResponse(BaseModel): # returns all available personas
    personas: Dict[str, PersonaCard]