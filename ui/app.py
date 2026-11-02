import os
import html
from datetime import date, datetime
from typing import Any, Dict, List

import requests
import streamlit as st

# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------
st.set_page_config(
    page_title="Health Insurance Policy Advisor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# Theme / CSS
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --navy: #09275d;
        --blue: #0868d7;
        --blue2: #e8f2ff;
        --border: #d8e5f5;
        --muted: #64748b;
        --panel: #ffffff;
        --green: #168348;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #10264e;
    }
    .stApp {
        background: linear-gradient(115deg, #f7faff 0%, #ffffff 58%, #f6faff 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #edf5ff 0%, #f7faff 100%);
        border-right: 1px solid #d9e6f5;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }
    .brand {
        display:flex; align-items:center; gap:12px;
        padding: 2px 4px 18px 4px; border-bottom:1px solid #d5e3f4;
        margin-bottom:14px;
    }
    .brand-shield {
        width:54px;height:62px;border-radius:16px 16px 22px 22px;
        background:linear-gradient(145deg,#1685ef,#0757bb);
        display:flex;align-items:center;justify-content:center;
        color:white;font-size:31px;font-weight:800;
        box-shadow:0 6px 14px #0b65c52a;
    }
    .brand-title {font-size:18px;font-weight:800;line-height:1.15;color:#09275d;}
    .brand-sub {font-size:11px;color:#31517f;margin-top:5px;}
    .side-section {
        font-size:14px;font-weight:800;color:#09275d;
        padding:14px 10px 8px 10px;
    }
    .side-note {
        background:#e8f7ee;border:1px solid #ccebd8;color:#14743e;
        border-radius:9px;padding:10px 12px;font-size:12px;font-weight:600;
        margin:8px 0 12px 0;
    }
    .main-title {font-size:32px;font-weight:800;letter-spacing:-.8px;color:#09275d;margin:0;}
    .main-subtitle {font-size:16px;color:#173b70;margin-top:3px;margin-bottom:12px;}
    .warning {
        background:#fff9e9;border:1px solid #f6e4b7;border-radius:12px;
        padding:10px 14px;color:#283b58;font-size:12px;margin:10px 0 18px 0;
    }
    .hero-side {
        height:100%; min-height:92px; display:flex; align-items:center;
        justify-content:center; gap:10px; color:#0b5fbe;
        background:linear-gradient(135deg,#f1f7ff,#e8f3ff);
        border-radius:18px;padding:12px;
    }
    .hero-shield {font-size:52px;}
    .hero-copy {font-size:17px;font-weight:800;line-height:1.25;color:#0a2b60;}
    .hero-copy span {font-size:13px;color:#0871d9;font-weight:600;}
    .quick-card {
        min-height:112px;background:#fff;border:1px solid #d9e6f5;border-radius:13px;
        padding:13px 12px;box-shadow:0 2px 8px #0b3c7410;
    }
    .quick-icon {font-size:24px;margin-bottom:5px;}
    .quick-title {font-size:13px;font-weight:800;color:#09275d;}
    .quick-desc {font-size:11px;color:#5c6f8c;margin-top:5px;line-height:1.35;}
    .panel {
        background:#fff;border:1px solid #d9e6f5;border-radius:15px;
        padding:15px;box-shadow:0 3px 12px #0b3c740a;margin-bottom:12px;
    }
    .panel-title {font-size:15px;font-weight:800;color:#09275d;margin-bottom:12px;}
    .summary-head {
        background:#eaf7ef;color:#14753e;border-radius:9px;
        padding:10px 12px;font-weight:800;margin-bottom:10px;
    }
    .summary-row {display:flex;justify-content:space-between;gap:8px;
        font-size:12px;padding:5px 2px;color:#243a5c;}
    .summary-row b {color:#09275d;}
    .source-item {
        background:#f7faff;border:1px solid #edf2f8;border-radius:10px;
        padding:10px;margin:8px 0;
    }
    .source-id {font-size:12px;font-weight:800;color:#09275d;}
    .source-name {font-size:12px;color:#263d63;margin-top:3px;}
    .source-meta {font-size:10px;color:#72819a;margin-top:4px;}
    .related {color:#0868d7;font-size:12px;padding:6px 0;line-height:1.35;}
    .chat-panel {
        background:rgba(255,255,255,.88);border:1px solid #d9e6f5;
        border-radius:16px;padding:14px 14px 8px 14px;min-height:480px;
    }
    .message-row {display:flex;gap:10px;align-items:flex-start;margin:4px 0 14px 0;}
    .avatar {
        width:38px;height:38px;min-width:38px;border-radius:50%;
        display:flex;align-items:center;justify-content:center;
        background:#e3f0ff;color:#075ec6;font-size:20px;font-weight:800;
    }
    .bubble {
        max-width:100%;background:#f0f2f5;border-radius:13px;
        padding:13px 15px;color:#172b4d;font-size:13px;line-height:1.6;
    }
    .user-row {display:flex;justify-content:flex-end;gap:10px;margin:12px 0 15px 0;}
    .user-bubble {
        max-width:78%;background:#dceeff;border:1px solid #c5e1fb;
        border-radius:13px;padding:12px 15px;color:#10264e;font-size:13px;line-height:1.5;
    }
    .timestamp {font-size:10px;color:#7c8ba5;margin-top:4px;}
    .answer-good {
        background:#eaf7ee;border:1px solid #d5efdd;border-radius:10px;
        padding:11px 12px;margin:9px 0;color:#164d30;font-size:12px;line-height:1.5;
    }
    .answer-info {
        background:#eaf3ff;border:1px solid #d8e9ff;border-radius:10px;
        padding:10px 12px;margin-top:12px;color:#174078;font-size:11px;line-height:1.5;
    }
    .stButton > button {
        border-radius:9px;border:1px solid #cbdcf0;font-weight:600;
        color:#0a3975;background:#fff;min-height:38px;
    }
    .stButton > button:hover {border-color:#0871d9;color:#075fc2;}
    div[data-testid="stChatInput"] {
        border:1px solid #9fc9f7;border-radius:13px;
        box-shadow:0 3px 12px #0b3c7410;
    }
    .footer {font-size:10px;color:#71819a;text-align:center;padding:10px 0;}
    @media (max-width: 900px) {
        .main-title {font-size:25px;}
        .hero-side {display:none;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! 👋\n\nI'm your Health Insurance Policy Advisor. I can help you "
                "understand your policy benefits, waiting periods, exclusions, and "
                "documentation requirements.\n\nYou can ask a question or choose one "
                "of the quick actions above."
            ),
            "sources": [],
            "topic": "Getting started",
            "status": "Ready",
        }
    ]

if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

# ------------------------------------------------------------
# Configuration and API adapter
# ------------------------------------------------------------
API_URL = os.getenv("POLICY_ADVISOR_API_URL", "http://localhost:8000/ask")
API_TIMEOUT = int(os.getenv("POLICY_ADVISOR_API_TIMEOUT", "45"))

def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)

def call_advisor_api(question: str, plan: str, version: str) -> Dict[str, Any]:
    """
    Expected request (adjust this function if your FastAPI Pydantic model differs):
      POST /ask
      {
        "question": "...",
        "plan_id": "silver",
        "version": "v2"
      }

    The response adapter accepts common field names:
      answer / response / final_answer
      sources / citations
      intent / topic
      status / answer_status
    """
    payload = {
        "question": question,
        "plan_id": plan.lower().replace(" ", "_"),
        "version": version.split(" ")[0],
    }
    response = requests.post(API_URL, json=payload, timeout=API_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    answer = (
        data.get("answer")
        or data.get("final_answer")
        or data.get("response")
        or data.get("message")
    )
    if not answer:
        answer = "The API responded, but no answer field was found. Please check the response schema."

    sources = data.get("sources") or data.get("citations") or data.get("retrieved_documents") or []
    if isinstance(sources, dict):
        sources = [sources]

    return {
        "answer": safe_text(answer),
        "sources": sources if isinstance(sources, list) else [],
        "topic": safe_text(data.get("intent") or data.get("topic"), "Policy question"),
        "status": safe_text(data.get("answer_status") or data.get("status"), "Grounded response"),
        "raw": data,
    }

def make_demo_answer(question: str, plan: str, version: str) -> Dict[str, Any]:
    """Local demo response used only when the FastAPI server is unavailable."""
    return {
        "answer": (
            f"Here is a demo response for **{plan} ({version})**.\n\n"
            "The exact coverage, waiting period, exclusions, and required documents "
            "must be confirmed from the applicable policy wording. Connect your "
            "FastAPI `/ask` endpoint to show policy-grounded answers and citations here."
        ),
        "sources": [
            {
                "id": "DEMO-POLICY-001",
                "title": "Benefits and Coverage",
                "plan": plan,
                "version": version.split(" ")[0],
            },
            {
                "id": "DEMO-WAIT-002",
                "title": "Waiting Periods",
                "plan": plan,
                "version": version.split(" ")[0],
            },
        ],
        "topic": "Coverage & Waiting Period",
        "status": "Demo mode — not retrieved from policy sources",
    }

def ask_advisor(question: str, plan: str, version: str) -> None:
    question = question.strip()
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    try:
        result = call_advisor_api(question, plan, version)
    except requests.RequestException as exc:
        # Demo fallback keeps the UI usable while the backend is being developed.
        result = make_demo_answer(question, plan, version)
        result["status"] = "Demo mode — API unavailable"
        st.session_state.api_error = str(exc)
    except (ValueError, TypeError) as exc:
        result = make_demo_answer(question, plan, version)
        result["status"] = "Demo mode — could not parse API response"
        st.session_state.api_error = str(exc)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "topic": result["topic"],
            "status": result["status"],
        }
    )
    st.session_state.last_answer = result

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
          <div class="brand-shield">✚</div>
          <div>
            <div class="brand-title">Health Insurance<br>Policy Advisor</div>
            <div class="brand-sub">Your Policy. Clear Answers. Always.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_items = ["💬  Chat", "▤  My Policy", "⇄  Compare Plans", "▣  FAQs", "▢  Feedback", "ⓘ  About"]
    selected_nav = st.radio(
        "Navigation",
        nav_items,
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown('<div class="side-section">✣ Select Your Policy</div>', unsafe_allow_html=True)

    plan = st.selectbox(
        "Plan",
        ["Silver Health Plan", "Gold Health Plan", "Platinum Health Plan"],
        index=0,
    )
    version = st.selectbox("Version", ["v2 (Active)", "v1 (Archived)"], index=0)
    st.date_input("Effective Date", value=date(2025, 1, 1), disabled=True)

    st.markdown(
        f'<div class="side-note">✓ &nbsp;{html.escape(plan)} ({html.escape(version.split()[0])}) selected</div>',
        unsafe_allow_html=True,
    )

    if st.button("＋  New Conversation", use_container_width=True, type="primary"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! 👋 Ask me anything about your selected policy.",
                "sources": [],
                "topic": "Getting started",
                "status": "Ready",
            }
        ]
        st.session_state.last_answer = None
        st.rerun()

    if st.button("▤  Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_answer = None
        st.rerun()

    st.markdown("---")
    st.markdown(
        '<div class="footer">✦ Powered by Microsoft Azure<br><br>Privacy &nbsp; | &nbsp; Terms &nbsp; | &nbsp; Help</div>',
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
header_left, header_right = st.columns([5, 1.25], vertical_alignment="center")
with header_left:
    st.markdown('<div class="main-title">Health Insurance Policy Advisor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Understand your benefits, waiting periods, exclusions and more — powered by AI.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="warning">⚠️ &nbsp; This is a fictional educational assistant. It does not guarantee claim approval or provide medical advice.</div>',
        unsafe_allow_html=True,
    )
with header_right:
    st.markdown(
        """
        <div class="hero-side">
          <div class="hero-shield">🛡️</div>
          <div class="hero-copy">Better<br>Information<br><span>Healthier Tomorrow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# Quick actions
# ------------------------------------------------------------
quick_actions = [
    ("🛡️", "Check Benefits", "What's covered in my plan?", "What benefits are covered under my selected plan?"),
    ("🕒", "Waiting Periods", "When can I claim certain benefits?", "What are the waiting periods in my selected plan?"),
    ("🚫", "Exclusions", "What is not covered?", "What exclusions should I know about in my selected plan?"),
    ("📄", "Required Documents", "What documents do I need?", "What documents are required to make a claim?"),
    ("⚖️", "Compare Plans", "See side-by-side benefits", "Compare the benefits of Silver and Gold plans."),
]
quick_cols = st.columns(5, gap="small")
for idx, (icon, title, desc, prompt) in enumerate(quick_actions):
    with quick_cols[idx]:
        st.markdown(
            f"""
            <div class="quick-card">
              <div class="quick-icon">{icon}</div>
              <div class="quick-title">{title} &nbsp; →</div>
              <div class="quick-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Ask", key=f"quick_{idx}", use_container_width=True):
            ask_advisor(prompt, plan, version)
            st.rerun()

st.write("")

# ------------------------------------------------------------
# Main chat + right information rail
# ------------------------------------------------------------
chat_col, rail_col = st.columns([2.25, 1], gap="medium")

with chat_col:
    st.markdown('<div class="panel-title">💬 Policy conversation</div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-panel">', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.info("Your chat is clear. Ask a policy question below or choose a quick action.")

    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(
                f"""
                <div class="user-row">
                  <div class="user-bubble">{html.escape(message["content"])}</div>
                  <div class="avatar">👤</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            safe_content = html.escape(message.get("content", "")).replace("\n", "<br>")
            st.markdown(
                f"""
                <div class="message-row">
                  <div class="avatar">🤖</div>
                  <div style="flex:1">
                    <div class="bubble">{safe_content}</div>
                    <div class="timestamp">{datetime.now().strftime("%I:%M %p")}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Show a grounded status and sources below the answer.
            if message.get("status") and message.get("status") != "Ready":
                st.caption(f"Answer status: {message['status']}")
            if message.get("sources"):
                with st.expander(f"📚 Sources used ({len(message['sources'])})", expanded=False):
                    for source in message["sources"]:
                        if isinstance(source, dict):
                            sid = source.get("id") or source.get("clause_id") or source.get("document_id") or "Policy source"
                            title = source.get("title") or source.get("name") or source.get("section") or "Policy clause"
                            st.markdown(f"**{safe_text(sid)}** — {safe_text(title)}")
                        else:
                            st.write(safe_text(source))

    st.markdown("</div>", unsafe_allow_html=True)

    question = st.chat_input("Type your question here...")
    if question:
        ask_advisor(question, plan, version)
        st.rerun()

with rail_col:
    latest_assistant = next(
        (m for m in reversed(st.session_state.messages) if m["role"] == "assistant" and m.get("status") != "Ready"),
        None,
    )
    topic = latest_assistant.get("topic", "Not selected") if latest_assistant else "Not selected"
    status = latest_assistant.get("status", "Waiting for a question") if latest_assistant else "Waiting for a question"
    sources = latest_assistant.get("sources", []) if latest_assistant else []

    st.markdown(
        f"""
        <div class="panel">
          <div class="summary-head">▤ &nbsp; Answer Summary</div>
          <div class="summary-row"><b>Plan</b><span>{html.escape(plan)}</span></div>
          <div class="summary-row"><b>Version</b><span>{html.escape(version)}</span></div>
          <div class="summary-row"><b>Topic</b><span>{html.escape(topic)}</span></div>
          <div class="summary-row"><b>Answer Status</b><span>🟢 {html.escape(status)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="panel"><div class="panel-title">🔗 Sources Used (' + str(len(sources)) + ')</div>', unsafe_allow_html=True)
    if sources:
        for source in sources[:5]:
            if isinstance(source, dict):
                sid = source.get("id") or source.get("clause_id") or source.get("document_id") or "Policy source"
                title = source.get("title") or source.get("name") or source.get("section") or "Policy clause"
                source_plan = source.get("plan") or plan.replace(" Health Plan", "")
                source_version = source.get("version") or version.split(" ")[0]
                st.markdown(
                    f"""
                    <div class="source-item">
                      <div class="source-id">📄 {html.escape(safe_text(sid))}</div>
                      <div class="source-name">{html.escape(safe_text(title))}</div>
                      <div class="source-meta">Plan: {html.escape(safe_text(source_plan))} | Version: {html.escape(safe_text(source_version))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<div class="source-item">{html.escape(safe_text(source))}</div>', unsafe_allow_html=True)
    else:
        st.caption("Sources returned by the API will appear here.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel"><div class="panel-title">💡 Related Questions</div>', unsafe_allow_html=True)
    related_questions = [
        f"What are the waiting periods in {plan.replace(' Health Plan', '')}?",
        "What documents are needed for a hospitalisation claim?",
        "Does the Gold plan have a shorter waiting period?",
        "What surgeries are covered under this policy?",
    ]
    for i, related in enumerate(related_questions):
        if st.button(f"➜  {related}", key=f"related_{i}", use_container_width=True):
            ask_advisor(related, plan, version)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption("Press Enter to send. Your answers should be checked against the official policy wording.")

# ------------------------------------------------------------
# Backend connection hint (collapsed)
# ------------------------------------------------------------
with st.expander("Backend connection settings"):
    st.write(f"FastAPI endpoint: `{API_URL}`")
    st.write("Set `POLICY_ADVISOR_API_URL` as an environment variable if your endpoint is different.")
    st.code(
        'payload = {"question": "...", "plan_id": "silver_health_plan", "version": "v2"}',
        language="python",
    )
    if "api_error" in st.session_state:
        st.warning(f"Latest API connection issue: {st.session_state.api_error}")
