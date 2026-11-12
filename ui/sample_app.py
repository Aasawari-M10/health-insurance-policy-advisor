import os
import base64
from datetime import datetime
from typing import Any, Dict
from urllib.parse import quote

import requests
import streamlit as st

st.set_page_config(page_title="Health Insurance Advisor", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

API_BASE_URL = os.getenv("POLICY_ADVISOR_API_BASE_URL", "http://localhost:8000").rstrip("/")
API_URL = f"{API_BASE_URL}/ask"
HEALTH_URL = f"{API_BASE_URL}/health"
COMPARE_API_URL = os.getenv("POLICY_ADVISOR_COMPARE_API_URL", f"{API_BASE_URL}/compare")
SUMMARY_API_URL = f"{API_BASE_URL}/policy-summary"  
API_TIMEOUT = int(os.getenv("POLICY_ADVISOR_API_TIMEOUT", "45"))

PLAN_ID_MAP = {"Silver Health Plan": "PLAN001", "Gold Health Plan": "PLAN002", "Platinum Health Plan": "PLAN003"}
CATEGORY_MAP = {"Benefits": "benefit", "Waiting Periods": "waiting_period", "Exclusions": "exclusion", "Required Documents": "documentation"}

SUGGESTED_QUESTIONS = {
    "home": [
        "What benefits are covered under my selected plan?",
        "What is the waiting period for my selected plan?",
        "What exclusions should I know about?",
        "What documents are required for hospitalization?",
    ],

    "benefits": [
        "What hospitalization benefits are covered under this plan?",
        "What room expenses are covered under this plan?",
        "What are the major benefits of this policy?",
        "What documents are required to claim hospitalization benefits?",
    ],

    "waiting": [
        "What is the waiting period for this policy?",
        "What is the waiting period for planned procedures?",
        "When will I become eligible for planned procedures?",
        "What waiting-period conditions should I know about?",
    ],

    "exclusions": [
        "What is not covered under this policy?",
        "Are cosmetic procedures covered?",
        "What are the major exclusions in this plan?",
        "Are there any exceptions to the exclusions?",
    ],

    "documents": [
        "Summarize the whole selected policy.",
        "What are the major benefits in this policy?",
        "What are the important exclusions in this policy?",
        "What is the waiting period in this policy?",
        "What documents are required under this policy?",
        "What are the most important things I should know about this policy?",
    ],
}


COMPARE_SUGGESTIONS = [
    {
        "question": "Compare the benefits of these two plans.",
        "category": "Benefits",
    },
    {
        "question": "Which plan has the shorter waiting period?",
        "category": "Waiting Periods",
    },
    {
        "question": "Compare the exclusions of these two plans.",
        "category": "Exclusions",
    },
    {
        "question": "Compare the required documents for these plans.",
        "category": "Required Documents",
    },
]
def init_state():
    defaults = {
        "dark_mode": False, "active_page": "home", "selected_plan": "Silver Health Plan",
        "selected_version": "v2 (Active)", "messages": [], "last_answer": None,
        "api_error": "", "comparison_result": None, "policy_pdf": None, "policy_pdf_name": None,
        "policy_summary": None,"policy_summary_document": None,
    }
    

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def safe_text(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


def source_fields(source: Any):
    if isinstance(source, dict):
        source_id = source.get("id") or source.get("clause_id") or source.get("document_id") or source.get("source_id") or "Policy source"
        title = source.get("title") or source.get("name") or source.get("section") or source.get("category") or "Policy clause"
        return safe_text(source_id), safe_text(title)
    return safe_text(source), "Supporting policy source"


def check_backend_health() -> bool:
    try:
        return requests.get(HEALTH_URL, timeout=3).status_code == 200
    except requests.RequestException:
        return False


def call_advisor_api(question: str, plan: str, version: str) -> Dict[str, Any]:
    plan_id = PLAN_ID_MAP[plan]
    policy_version = version.split(" ")[0]
    response = requests.post(API_URL, json={"question": question, "plan_id": plan_id, "version": policy_version}, timeout=API_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    answer = data.get("answer")
    if not answer:
        raise ValueError("FastAPI returned no answer.")
    sources = data.get("source_clauses") or data.get("sources") or data.get("citations") or []
    if isinstance(sources, dict):
        sources = [sources]
    if not isinstance(sources, list):
        sources = []
    intent = safe_text(data.get("intent"), "Policy question")
    answer_lower = safe_text(answer).lower()
    status = "Grounded response" if sources else ("Human review required" if intent == "escalation" or "human review" in answer_lower or "cannot guarantee" in answer_lower else "Guarded response")
    return {"answer": safe_text(answer), "sources": sources, "topic": intent, "status": status, "raw": data}


def ask_advisor(question: str):
    question = question.strip()
    if not question:
        return
    st.session_state.messages.append({"role": "user", "content": question, "timestamp": datetime.now().strftime("%I:%M %p")})
    try:
        result = call_advisor_api(question, st.session_state.selected_plan, st.session_state.selected_version)
        st.session_state.api_error = ""
        st.session_state.messages.append({"role": "assistant", "content": result["answer"], "sources": result["sources"], "topic": result["topic"], "status": result["status"], "timestamp": datetime.now().strftime("%I:%M %p")})
        st.session_state.last_answer = result
    except requests.Timeout:
        st.session_state.api_error = "FastAPI request timed out."
        st.session_state.messages.append({"role": "assistant", "content": "The policy advisor took too long to respond. Please try again.", "sources": [], "status": "Backend timeout", "timestamp": datetime.now().strftime("%I:%M %p")})
    except requests.RequestException as exc:
        st.session_state.api_error = str(exc)
        st.session_state.messages.append({"role": "assistant", "content": "The policy advisor backend is currently unavailable.", "sources": [], "status": "Backend unavailable", "timestamp": datetime.now().strftime("%I:%M %p")})
    except (ValueError, TypeError, KeyError) as exc:
        st.session_state.api_error = str(exc)
        st.session_state.messages.append({"role": "assistant", "content": "The backend returned an unexpected response.", "sources": [], "status": "Invalid API response", "timestamp": datetime.now().strftime("%I:%M %p")})


def call_comparison_api(plan_a, version_a, plan_b, version_b, category):
    payload = {"question": f"Compare the {category.lower()} of {plan_a} and {plan_b}.", "plan_a_id": PLAN_ID_MAP[plan_a], "plan_a_version": version_a.split(" ")[0], "plan_b_id": PLAN_ID_MAP[plan_b], "plan_b_version": version_b.split(" ")[0], "category": CATEGORY_MAP[category], "top": 3}
    response = requests.post(COMPARE_API_URL, json=payload, timeout=API_TIMEOUT)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60, show_spinner=False)
def get_policy_documents():
    try:
        response = requests.get(f"{API_BASE_URL}/policy-documents", timeout=30)
        response.raise_for_status()
        return response.json().get("documents", [])
    except requests.RequestException:
        return []


def get_policy_document(filename: str):
    try:
        response = requests.get(f"{API_BASE_URL}/policy-documents/{quote(filename, safe='')}", timeout=30)
        response.raise_for_status()
        return response.content
    except requests.RequestException as exc:
        st.error(f"Unable to load policy document: {exc}")
        return None


def display_pdf(pdf_bytes: bytes):
    encoded = base64.b64encode(pdf_bytes).decode("utf-8")
    st.markdown(f'<iframe src="data:application/pdf;base64,{encoded}" width="100%" height="680" type="application/pdf"></iframe>', unsafe_allow_html=True)
def get_policy_summary(document_path: str):
    try:
        response = requests.post(
            SUMMARY_API_URL,
            json={
                "document_path": document_path
            },
            timeout=API_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("summary"):
            raise ValueError(
                "Backend returned no policy summary."
            )

        return data

    except requests.RequestException as exc:
        st.error(
            f"Unable to summarize policy: {exc}"
        )
        return None

def go(page: str):
    st.session_state.active_page = page

def render_question_suggestions(
    section: str,
    *,
    redirect_to_chat: bool = True,
):
    """
    Display clickable reference questions for a section.

    Clicking a question sends it through the existing advisor API.
    """

    questions = SUGGESTED_QUESTIONS.get(
        section,
        [],
    )

    if not questions:
        return

    st.markdown(
        """
        <div class="suggestion-heading">
            💡 Suggested questions
        </div>

        <div class="suggestion-subtitle">
            Select a question to ask the advisor.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="suggestion-area">',
        unsafe_allow_html=True,
    )

    columns = st.columns(2, gap="small")

    for index, question in enumerate(questions):
        column = columns[index % 2]

        with column:
            if st.button(
                question,
                key=f"suggestion_{section}_{index}",
                use_container_width=True,
            ):
                ask_advisor(question)

                if redirect_to_chat:
                    st.session_state.active_page = "home"

                st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

dark = st.session_state.dark_mode
C = ({"bg":"#111124","surface":"#19172e","surface2":"#24203e","text":"#f7f4ff","muted":"#b9b1d1","border":"#3d3562","input":"#211d38","shadow":"rgba(0,0,0,.35)"} if dark else {"bg":"#f4efff","surface":"rgba(255,255,255,.84)","surface2":"#ffffff","text":"#18132d","muted":"#6e6782","border":"#d9cff2","input":"#ffffff","shadow":"rgba(76,43,130,.14)"})

st.markdown(
    f"""
<style>

:root {{
    --bg:{C['bg']};
    --surface:{C['surface']};
    --surface2:{C['surface2']};
    --text:{C['text']};
    --muted:{C['muted']};
    --border:{C['border']};
    --input:{C['input']};
    --shadow:{C['shadow']};
}}

* {{
    box-sizing: border-box;
}}

html,
body,
[class*="css"] {{
    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        "Segoe UI",
        sans-serif;
}}


/* ============================================================
   GLOBAL APP
   ============================================================ */

.stApp {{
    color: var(--text);

    background:
        radial-gradient(
            circle at 86% 12%,
            rgba(184,148,255,.24),
            transparent 25%
        ),
        radial-gradient(
            circle at 28% 82%,
            rgba(150,105,241,.18),
            transparent 28%
        ),
        linear-gradient(
            145deg,
            var(--bg),
            #faf8ff 60%,
            var(--bg)
        );
}}


/* ============================================================
   STREAMLIT HEADER
   ============================================================ */

[data-testid="stHeader"] {{
    background: transparent !important;
    z-index: 1001 !important;
}}


/* ============================================================
   MAIN CONTENT
   ============================================================ */

[data-testid="stMainBlockContainer"] {{
    max-width: 1500px;
    padding:
        0
        1.4rem
        2rem
        1.4rem;
}}


/* ============================================================
   TOP BAR
   Full browser width, including above sidebar
   ============================================================ */

.topbar {{

    position: fixed;

    top: 0;
    left: 0;
    right: 0;

    width: 100%;

    height: 90px;
    min-height: 90px;

    display: flex;

    align-items: center;
    justify-content: center;

    padding: 10px 30px;

    margin: 0;

    background:
        linear-gradient(
            110deg,
            #4d2787,
            #6c3bb1 45%,
            #3e176d
        );

    color: white;

    box-shadow:
        0 3px 16px
        rgba(54,26,104,.25);

    z-index: 1000;
}}


.topbrand {{
    display: flex;
    align-items: center;
    gap: 13px;
}}


.topshield {{

    width: 42px;
    height: 48px;

    border: 4px solid white;

    border-radius:
        13px
        13px
        17px
        17px;

    display: grid;
    place-items: center;

    font-size: 25px;
    font-weight: 900;
}}


.toptitle {{
    font-size: 23px;
    font-weight: 850;
    line-height: 1.05;
}}


.topsub {{
    font-size: 13px;
    opacity: .85;
    margin-top: 4px;
}}


/* ============================================================
   PUSH MAIN CONTENT BELOW FIXED HEADER
   ============================================================ */

[data-testid="stAppViewContainer"] > .main {{

    padding-top: 90px;

}}


/* Alternative newer Streamlit structure */

[data-testid="stMain"] {{

    padding-top: 90px;

}}


/* ============================================================
   SIDEBAR
   Starts BELOW purple topbar
   ============================================================ */

[data-testid="stSidebar"] {{

    top: 90px !important;

    height:
        calc(100vh - 50px) !important;

    background:
        var(--surface) !important;

    border-right:
        1px solid
        var(--border);

    z-index: 900 !important;
}}


[data-testid="stSidebar"] > div:first-child {{

    padding-top: 18px;

}}


[data-testid="stSidebar"] * {{

    color:
        var(--text);

}}


/* ============================================================
   SIDEBAR CONTENT
   ============================================================ */

.side-pad {{

    padding:
        18px
        17px;

}}


.side-btn
.stButton
button {{

    min-height:
        43px;

    justify-content:
        flex-start;

    border-radius:
        10px;

    

    border:
        1.5px solid
        #7742c7 !important;
    color:
        #161127 !important;

    font-weight:
        750;
}}


.side-btn.b1
.stButton
button {{

    background:
        linear-gradient(
            90deg,
            #fff2c9,
            #ffe7ae
        );
    border:
        1.5px solid
        #7742c7 !important;

}}


.side-btn.b2
.stButton
button {{

    background:
        linear-gradient(
            90deg,
            #dff7e8,
            #ccefe0
        );

}}


.side-btn.b3
.stButton
button {{

    background:
        linear-gradient(
            90deg,
            #e4efff,
            #d4e5ff
        );

}}


.side-btn.b4
.stButton
button {{

    background:
        linear-gradient(
            90deg,
            #ffe8e6,
            #ffdcd8
        );

}}


.side-btn.b5
.stButton
button {{

    background:
        linear-gradient(
            90deg,
            #eee4ff,
            #dccbff
        );

}}


.side-illustration {{

    text-align:
        center;

    font-size:
        74px;

    padding:
        32px
        0
        25px;

    filter:
        drop-shadow(
            0
            8px
            10px
            rgba(90,55,160,.2)
        );

}}


.newchat
.stButton
button {{

    background:
        linear-gradient(
            135deg,
            #6732b7,
            #451b86
        );

    color:
        white !important;

    border:
        1.5px solid
        #7742c7 !important;

    border-radius:
        12px;

    font-weight:
        800;

    min-height:
        43px;

}}


/* ============================================================
   HERO
   ============================================================ */

.hero-shell {{

    margin-top:
        0;

    min-height:
        calc(100vh - 90px);

    padding:
        55px
        25px
        18px;

    border:
        1px solid
        var(--border);

    border-radius:
        0
        0
        22px
        22px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.68),
            rgba(248,244,255,.9)
        );

    box-shadow:
        0
        8px
        26px
        var(--shadow);

    position:
        relative;

    overflow:
        hidden;
}}


.hero-shell:before {{

    content:
        "";

    position:
        absolute;

    width:
        560px;

    height:
        180px;

    right:
        -110px;

    top:
        -70px;

    background:
        rgba(183,148,255,.20);

    border-radius:
        50%;

    transform:
        rotate(-14deg);
}}


.hero-shell:after {{

    content:
        "";

    position:
        absolute;

    width:
        500px;

    height:
        300px;

    left:
        -150px;

    bottom:
        -90px;

    background:
        rgba(162,119,236,.16);

    border-radius:
        50%;

    transform:
        rotate(12deg);
}}


/* ============================================================
   HERO IMAGE
   IMPORTANT FIX:
   Adds space between topbar and umbrella/image
   ============================================================ */

.hero-art {{

    position:
        relative;

    z-index:
        1;

    text-align:
        center;

    font-size:
        94px;

    line-height:
        1;

    margin-top:
        200px;

    margin-bottom:
        15px;

    filter:
        drop-shadow(
            0
            12px
            12px
            rgba(92,52,173,.16)
        );
}}


/* ============================================================
   HERO TEXT
   ============================================================ */

.hero-title {{

    position:
        relative;

    z-index:
        1;

    text-align:
        center;

    font-size:
        28px;

    font-weight:
        880;

    color:
        #32166f;

    margin-top:
        4px;
}}


.hero-sub {{

    position:
        relative;

    z-index:
        1;

    text-align:
        center;

    font-size:
        14px;

    color:
        #6f6880;

    max-width:
        680px;

    margin:
        8px
        auto
        25px;

    line-height:
        1.55;
}}


/* ============================================================
   HOME ACTION CARDS
   ============================================================ */

.action-card {{

    position:
        relative;

    z-index:
        1;

    min-height:
        94px;

    border:
        1px solid
        #ded4f1;

    border-radius:
        14px;

    background:
        rgba(255,255,255,.72);

    padding:
        14px
        8px;

    text-align:
        center;

    box-shadow:
        0
        5px
        13px
        rgba(87,50,148,.09);
}}


.action-icon {{

    font-size:
        27px;

    color:
        #6331be;

}}


.action-title {{

    font-size:
        13px;

    font-weight:
        800;

    color:
        #1a1430;

    line-height:
        1.15;

    margin-top:
        6px;

}}


/* ============================================================
   BUTTONS
   ============================================================ */

.stButton button {{

    border-radius:
        11px;

    border:
        1px solid
        var(--border);

    background:
        var(--surface2);

    color:
        var(--text);

    font-weight:
        700;
}}


.stButton
button[kind="primary"] {{

    background:
        linear-gradient(
            135deg,
            #6d37c4,
            #431276
        );

    border:
        0;

    color:
        white;
}}


/* ============================================================
   CHAT
   ============================================================ */

.chat-wrap {{

    position:
        relative;

    z-index:
        2;

    margin-top:
        20px;

}}


.conversation-shell {{

    position:
        relative;

    z-index:
        2;

    padding:
        30px
        8px
        8px;

}}


.conversation-header {{

    margin-bottom:
        14px;

}}


.conversation-title {{

    font-size:
        24px;

    font-weight:
        850;

    color:
        var(--text);

}}


.conversation-subtitle {{

    margin-top:
        4px;

    font-size:
        13px;

    color:
        var(--muted);

}}


/* ============================================================
   CHAT MESSAGES
   ============================================================ */

[data-testid="stChatMessage"] {{
    background: var(--surface);

    border:
        1px solid
        var(--border);

    border-radius:
        14px;

    padding:
        10px
        13px;
}}


/* ============================================================
   CHAT INPUT OUTER AREA
   Same light surface as hero area
   ============================================================ */

[data-testid="stChatInput"] {{
    width: 100% !important;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.68),
            rgba(248,244,255,.9)
        ) !important;

    border:
        1.5px solid
        #7742c7 !important;

    border-radius:
        10px !important;

    padding:
        8px !important;

    box-shadow:
        0
        4px
        14px
        var(--shadow) !important;
}}


/* ============================================================
   INNER CHAT INPUT
   Make everything inside completely white
   ============================================================ */

[data-testid="stChatInput"] > div {{
    background:
        #ffffff !important;

    border-radius:
        7px !important;
}}


/* ============================================================
   TEXTAREA
   White background behind and under text
   ============================================================ */

[data-testid="stChatInput"] textarea {{
    background:
        #ffffff !important;

    color:
        #18132d !important;

    border:
        none !important;

    box-shadow:
        none !important;
}}


/* Placeholder text */

[data-testid="stChatInput"] textarea::placeholder {{
    color:
        #8b8598 !important;

    opacity:
        1 !important;
}}


/* ============================================================
   CHAT INPUT BUTTON AREA
   Keep complete inner row white
   ============================================================ */

[data-testid="stChatInput"]
[data-baseweb="textarea"] {{
    background:
        #ffffff !important;
}}


[data-testid="stChatInput"]
[data-baseweb="base-input"] {{
    background:
        #ffffff !important;
}}


/* ============================================================
   SEND BUTTON
   ============================================================ */

[data-testid="stChatInput"] button {{
    border-radius:
        8px !important;

    background:
        #f0ecf7 !important;

    color:
        #6331be !important;
}}


[data-testid="stChatInput"] button:hover {{
    background:
        #e5dcf5 !important;
}}

/* ============================================================
   OTHER STREAMLIT ELEMENTS
   ============================================================ */

[data-testid="stVerticalBlockBorderWrapper"] {{

    background:
        var(--surface);

    border-color:
        var(--border) !important;

    border-radius:
        15px !important;

}}


[data-baseweb="select"] > div,
input,
textarea {{

    background:
        var(--surface2) !important;

    color:
        var(--text) !important;

    border-color:
        var(--border) !important;

}}


.page-title {{

    font-size:
        28px;

    font-weight:
        850;

    color:
        var(--text);

    margin:
        35px
        0
        4px;

}}


.page-sub {{

    color:
        var(--muted);

    margin-bottom:
        18px;

}}


.status-ok {{

    color:
        #147d48;

    font-weight:
        800;

    font-size:
        12px;

}}


.status-bad {{

    color:
        #bb3347;

    font-weight:
        800;

    font-size:
        12px;

}}
/* ============================================================
   SUGGESTED QUESTIONS
   ============================================================ */

.suggestion-heading {{
    margin-top: 18px;
    margin-bottom: 5px;
    font-size: 15px;
    font-weight: 850;
    color: var(--text);
}}

.suggestion-subtitle {{
    margin-bottom: 10px;
    font-size: 12px;
    color: var(--muted);
}}

/*
Suggestion buttons use their own container so their appearance
can be adjusted without changing the sidebar navigation.
*/
.suggestion-area [data-testid="stButton"] button {{
    min-height: 45px;
    height: auto;
    padding: 9px 13px;
    justify-content: flex-start;
    text-align: left;
    white-space: normal;
    line-height: 1.3;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.94),
            rgba(244,237,255,.92)
        );

    border:
        1px solid
        #d8c8f2 !important;

    border-radius: 11px;
    color: var(--text) !important;
    font-size: 13px;
    font-weight: 650;

    box-shadow:
        0 3px 9px
        rgba(82,45,145,.07);
}}

.suggestion-area [data-testid="stButton"] button:hover {{
    border-color:
        #7742c7 !important;

    background:
        linear-gradient(
            135deg,
            #f7f1ff,
            #eadcff
        );

    transform:
        translateY(-1px);

    box-shadow:
        0 5px 12px
        rgba(82,45,145,.13);
}}

/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width:850px) {{

    .topbar {{
        justify-content:
            flex-start;

        padding-left:
            65px;
    }}

    .hero-title {{
        font-size:
            23px;
    }}

    .hero-art {{
        font-size:
            75px;

        margin-top:
            20px;
    }}

}}

</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="side-pad">', unsafe_allow_html=True)
    for css_class, label, page in [("b1","🛡️  Check Benefits","benefits"),("b2","🗓️  Waiting Period","waiting"),("b3","⊘  Exclusions","exclusions"),("b4","⚖️  Compare Plans","compare"),("b5","📄  View Policy Documents","documents")]:
        st.markdown(f'<div class="side-btn {css_class}">', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{page}", use_container_width=True):
            go(page); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    # st.markdown('<div class="side-illustration">🛡️📋💗</div>', unsafe_allow_html=True)
    st.selectbox("Plan", list(PLAN_ID_MAP), key="selected_plan")
    st.selectbox("Version", ["v2 (Active)", "v1 (Archived)"], key="selected_version")
    # st.toggle("Dark mode", key="dark_mode")
    st.markdown('<div class="newchat">', unsafe_allow_html=True)
    if st.button("💬  New Chat", use_container_width=True):
        st.session_state.messages = []; st.session_state.last_answer = None; st.session_state.active_page = "home"; st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('<div class="topbar"><div class="topbrand"><div class="topshield">✚</div><div><div class="toptitle">Health Insurance Advisor</div><div class="topsub">Your AI Assistant for Health Insurance Policies</div></div></div></div>', unsafe_allow_html=True)
backend_online = check_backend_health()


def render_messages():
    for message in st.session_state.messages:
        role = message.get("role", "assistant")
        with st.chat_message(role, avatar="👤" if role == "user" else "🛡️"):
            st.markdown(message.get("content", ""))
            if message.get("timestamp"):
                st.caption(message["timestamp"])
            if role == "assistant" and message.get("status"):
                st.caption(f"Answer status: {message['status']}")
            sources = message.get("sources", []) or []
            if sources:
                with st.expander(f"📚 Supporting clauses ({len(sources)})"):
                    for source in sources:
                        sid, title = source_fields(source)
                        st.markdown(f"**{sid}** · {title}")


def render_home():
    conversation_started = bool(st.session_state.messages)
    if not conversation_started:
        # st.markdown('<div class="hero-shell">', unsafe_allow_html=True)
        st.markdown('<div class="hero-art"></div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Welcome to Health Insurance Advisor</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">Ask anything about your health insurance policy, including benefits, waiting periods, exclusions, plan comparison and policy documents.</div>', unsafe_allow_html=True)
        cards = [("🛡️","Understand<br>Your Benefits","What benefits are covered under my selected plan?"),("🗓️","Check<br>Waiting Periods","What are the waiting periods in my selected plan?"),("⊘","Know<br>Exclusions","What exclusions should I know about in my selected plan?"),("⚖️","Compare<br>Insurance Plans",None)]
        cols = st.columns(4, gap="medium")
        render_question_suggestions(
            "home",
            redirect_to_chat=True,
        )
        question = st.chat_input("Ask about your health insurance policy...", key="welcome_chat_input")
        if question:
            ask_advisor(question); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown('<div class="conversation-shell"><div class="conversation-header"><div class="conversation-title">💬 Policy Conversation</div><div class="conversation-subtitle">Ask follow-up questions about your selected policy.</div></div>', unsafe_allow_html=True)
    # Scroll is created only after the first prompt. It activates when content exceeds 540px.
    with st.container(height=540, border=False):
        render_messages()
    question = st.chat_input("Ask a follow-up question about your policy...", key="conversation_chat_input")
    if question:
        ask_advisor(question); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_topic(
    title: str,
    prompt: str,
    section: str,
):
    st.markdown(
        f"""
        <div class="page-title">
            {title}
        </div>

        <div class="page-sub">
            Answers use the currently selected plan and version.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_question_suggestions(
        section,
        redirect_to_chat=True,
    )

    st.markdown("")

    if st.button(
        "Ask the advisor",
        type="primary",
        key=f"ask_advisor_{section}",
    ):
        ask_advisor(prompt)
        st.session_state.active_page = "home"
        st.rerun()

    question = st.chat_input(
        "Ask your own question about this topic...",
        key=f"topic_chat_input_{section}",
    )

    if question:
        ask_advisor(question)
        st.session_state.active_page = "home"
        st.rerun()


def render_compare():
    st.markdown('<div class="page-title">⚖️ Compare Health Plans</div><div class="page-sub">Choose two plan versions and compare grounded policy clauses.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        plan_a = st.selectbox("Plan A", list(PLAN_ID_MAP), index=0); version_a = st.selectbox("Plan A version", ["v2 (Active)", "v1 (Archived)"], index=1)
    with c2:
        plan_b = st.selectbox("Plan B", list(PLAN_ID_MAP), index=1); version_b = st.selectbox("Plan B version", ["v2 (Active)", "v1 (Archived)"], index=1)
    category = st.selectbox("Comparison category", list(CATEGORY_MAP))
    if st.button("Compare Plans", type="primary", use_container_width=True):
        if plan_a == plan_b and version_a == version_b: st.warning("Select two different policies or versions.")
        else:
            try:
                with st.spinner("Comparing policy evidence..."): st.session_state.comparison_result = call_comparison_api(plan_a, version_a, plan_b, version_b, category)
            except requests.RequestException as exc:
                st.error("The comparison service could not be reached."); st.session_state.api_error = str(exc)
    result = st.session_state.comparison_result
    if result:
        rows = result.get("comparison_rows") or []
        if rows: st.dataframe([{"Feature":r.get("feature",""),plan_a:r.get("plan_a",""),plan_b:r.get("plan_b",""),"Difference":r.get("difference","")} for r in rows], use_container_width=True, hide_index=True)
        if result.get("summary"): st.info(result["summary"])
        s1, s2 = st.columns(2)
        with s1:
            st.markdown(f"#### Sources: {plan_a}")
            for source in result.get("sources_a") or []: st.success(f"📄 {source}")
        with s2:
            st.markdown(f"#### Sources: {plan_b}")
            for source in result.get("sources_b") or []: st.success(f"📄 {source}")


def render_documents():

    st.markdown(
        '<div class="page-title">'
        '📄 Policy Documents'
        '</div>'
        '<div class="page-sub">'
        'View, summarize and download policy documents.'
        '</div>',
        unsafe_allow_html=True,
    )

    documents = get_policy_documents()

    if not documents:
        st.info(
            "No policy documents are currently available."
        )
        return

    selected = st.selectbox(
        "Select a policy document",
        documents,
        format_func=lambda p: p.split("/")[-1],
    )

    # Clear summary when another PDF is selected
    if (
        st.session_state.policy_summary_document
        and
        st.session_state.policy_summary_document != selected
    ):
        st.session_state.policy_summary = None
        st.session_state.policy_summary_document = None

    # -----------------------------------------
    # SIDE-BY-SIDE ACTION BUTTONS
    # -----------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        view_clicked = st.button(
            "📄 View Policy Document",
            type="primary",
            use_container_width=True,
        )

    with col2:

        summarize_clicked = st.button(
            "✨ Summarize Policy Document",
            type="primary",
            use_container_width=True,
        )

    # -----------------------------------------
    # VIEW PDF
    # -----------------------------------------

    if view_clicked:

        pdf = get_policy_document(
            selected
        )

        if pdf:
            st.session_state.policy_pdf = pdf
            st.session_state.policy_pdf_name = selected

    # -----------------------------------------
    # SUMMARIZE PDF
    # -----------------------------------------

    if summarize_clicked:

        with st.spinner(
            "Analyzing the complete policy document..."
        ):

            result = get_policy_summary(
                selected
            )

        if result:

            st.session_state.policy_summary = result

            st.session_state.policy_summary_document = (
                selected
            )

    # -----------------------------------------
    # SUMMARY
    # -----------------------------------------

    if (
        st.session_state.policy_summary
        and
        st.session_state.policy_summary_document == selected
    ):

        result = st.session_state.policy_summary

        st.markdown("---")

        st.markdown(
            "### ✨ Policy Summary"
        )

        st.markdown(
            result["summary"]
        )

        st.caption(
            "Summary generated from the complete "
            "policy document using Azure Document "
            "Intelligence and the Foundry model."
        )

    # -----------------------------------------
    # PDF VIEWER
    # -----------------------------------------

    if (
        st.session_state.policy_pdf
        and
        st.session_state.policy_pdf_name == selected
    ):

        st.markdown("---")

        display_pdf(
            st.session_state.policy_pdf
        )

        st.download_button(
            "⬇️ Download Policy Document",
            data=st.session_state.policy_pdf,
            file_name=selected.split("/")[-1],
            mime="application/pdf",
        )
page = st.session_state.active_page

if page == "home":
    render_home()

elif page == "benefits":
    render_topic(
        "🛡️ Check Benefits",
        "What benefits are covered under my selected plan?",
        "benefits",
    )

elif page == "waiting":
    render_topic(
        "🗓️ Waiting Period",
        "What are the waiting periods in my selected plan?",
        "waiting",
    )

elif page == "exclusions":
    render_topic(
        "⊘ Exclusions",
        "What exclusions should I know about in my selected plan?",
        "exclusions",
    )

elif page == "compare":
    render_compare()

elif page == "documents":
    render_documents()
with st.expander("⚙️ Backend connection details"):
    st.markdown('<div class="status-ok">● FastAPI backend connected</div>' if backend_online else '<div class="status-bad">● FastAPI backend unavailable</div>', unsafe_allow_html=True)
    st.code(API_BASE_URL)
    if st.session_state.api_error: st.warning(st.session_state.api_error)
