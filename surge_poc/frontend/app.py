import streamlit as st
import requests

API = "http://127.0.0.1:8000" # backend API URL

st.set_page_config(page_title="Surge-Staffing PoC", layout="wide") # set page config

if "session_id" not in st.session_state: # initialize session state
    st.session_state.session_id = None
    st.session_state.chat = []
    st.session_state.last_reply = ""

st.title("Hospital Surge Staffing — Stakeholder Interview PoC")

with st.sidebar: # sidebar for session management
    st.subheader("Session")
    seed = st.number_input("Seed", min_value=0, value=42) 
    if st.button("Start / Reset Session", use_container_width=True):
        r = requests.post(f"{API}/session", json={"seed": int(seed)})
        r.raise_for_status()
        data = r.json()
        st.session_state.session_id = data["session_id"]
        st.session_state.chat = []
        st.success(f"Session started: {data['session_id']}")

    st.markdown("---")
    st.subheader("Pin last answer")
    bucket = st.selectbox("Bucket", [
        "constraints","states","actions","transitions","rewards","uncertainties","tradeoffs"
    ])
    if st.button("Pin", use_container_width=True, disabled=st.session_state.session_id is None):
        if st.session_state.last_reply:
            requests.post(f"{API}/pin", json={
                "session_id": st.session_state.session_id,
                "bucket": bucket,
                "text": st.session_state.last_reply,
                "citations": [],
            })
            st.toast("Pinned to notes.")

    st.markdown("---")
    if st.session_state.session_id:
        notes = requests.get(f"{API}/notes", params={"session_id": st.session_state.session_id}).json()
        with st.expander("Notes (live)", expanded=True):
            for k, items in notes.get("notes", {}).items():
                st.write(f"**{k.capitalize()}**")
                for it in items:
                    st.write("- ", it["text"])

# main area for chat interface
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Meeting Room")
    if not st.session_state.session_id:
        st.info("Start a session from the sidebar.")
    else:
        r = requests.get(f"{API}/personas")
        personas = r.json()["personas"]
        with st.expander("Persona cards", expanded=False):
            for key, card in personas.items():
                st.write(f"**@{key} — {card['role']} ({card['name']})**. Temperament: {card['temperament']}")

        mention = st.selectbox("@mention", ["auto", "cfo", "physician", "manager"], index=0)
        prompt = st.text_input("Ask a focused question", "@CFO How would an extra surge team affect this month's budget?")
        if st.button("Send", use_container_width=True):
            payload = {"session_id": st.session_state.session_id, "persona": mention, "message": prompt}
            rr = requests.post(f"{API}/chat", json=payload)
            rr.raise_for_status()
            data = rr.json()
            st.session_state.chat.append(("user", prompt))
            st.session_state.chat.append((data["persona"], data["reply"]))
            st.session_state.last_reply = data["reply"]

        for role, text in st.session_state.chat[-12:]:
            if role == "user":
                st.chat_message("user").write(text)
            else:
                st.chat_message("assistant").write(f"**@{role}**: {text}")
with col2:
    st.subheader("Problem Formulation Canvas")
    st.caption("Pin facts from answers into these buckets via the sidebar.")
    tabs = st.tabs(["Constraints","States","Actions","Transitions","Rewards","Uncertainties","Trade-offs"])
    bucket_keys = ["constraints","states","actions","transitions","rewards","uncertainties","tradeoffs"]
    if st.session_state.session_id:
        notes = requests.get(f"{API}/notes", params={"session_id": st.session_state.session_id}).json()
        for t, k in zip(tabs, bucket_keys):
            with t:
                for it in notes.get("notes", {}).get(k, []):
                    st.write("- ", it["text"])
    else:
        st.info("Start a session to populate notes.")