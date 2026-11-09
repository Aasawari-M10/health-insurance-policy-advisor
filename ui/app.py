import os
import html
from datetime import date, datetime
from typing import Any, Dict
from urllib.parse import quote
import base64
import requests
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Health Insurance Policy Advisor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# SESSION STATE
# ============================================================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm your Health Insurance Policy Advisor.\n\n"
                "I can help explain benefits, waiting periods, exclusions, "
                "required documents and differences between policy versions. "
                "Choose a quick question or type your own question below."
            ),
            "sources": [],
            "topic": "Getting started",
            "status": "Ready",
            "timestamp": datetime.now().strftime("%I:%M %p"),
        }
    ]

if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

if "api_error" not in st.session_state:
    st.session_state.api_error = ""

# ============================================================
# GLOBAL THEME TOKENS — ENTIRE APP SWITCHES TOGETHER
# ============================================================
if st.session_state.dark_mode:
    T = {
        "app_bg": "#0b1220",
        "app_bg_2": "#101b2e",
        "sidebar_bg": "#101a2b",
        "panel": "#142238",
        "panel_alt": "#192b43",
        "panel_soft": "#1b304d",
        "text": "#e8f0ff",
        "text_soft": "#c0cde0",
        "muted": "#93a6c2",
        "border": "#2a4160",
        "blue": "#70aaff",
        "blue_deep": "#276bd1",
        "blue_soft": "#1b3659",
        "green": "#67d49a",
        "green_soft": "#173d32",
        "warning_bg": "#44371d",
        "warning_border": "#79602a",
        "warning_text": "#f7e4b0",
        "user_bubble": "#1b3c68",
        "assistant_bubble": "#192b43",
        "input_bg": "#142238",
        "shadow": "rgba(0,0,0,.24)",
        "hero_bg": "linear-gradient(135deg,#172b49,#1a3b65)",
        "quick_1": "linear-gradient(135deg,#172f50,#1a3d66)",
        "quick_2": "linear-gradient(135deg,#2b2148,#3a2a5b)",
        "quick_3": "linear-gradient(135deg,#40232d,#512b38)",
        "quick_4": "linear-gradient(135deg,#153d3d,#1b4b4a)",
        "quick_5": "linear-gradient(135deg,#33264b,#44305f)",
    }
else:
    T = {
        "app_bg": "#f4f7fd",
        "app_bg_2": "#ffffff",
        "sidebar_bg": "#edf3ff",
        "panel": "#ffffff",
        "panel_alt": "#f7faff",
        "panel_soft": "#eef4ff",
        "text": "#10234b",
        "text_soft": "#30496f",
        "muted": "#6c7e99",
        "border": "#d9e4f4",
        "blue": "#1767ce",
        "blue_deep": "#104fb0",
        "blue_soft": "#e8f1ff",
        "green": "#16834b",
        "green_soft": "#e9f7ef",
        "warning_bg": "#fff8e8",
        "warning_border": "#f0dfb4",
        "warning_text": "#5e4b1d",
        "user_bubble": "#e5efff",
        "assistant_bubble": "#f5f7fb",
        "input_bg": "#ffffff",
        "shadow": "rgba(31,73,125,.09)",
        "hero_bg": "linear-gradient(135deg,#edf5ff,#e2efff)",
        "quick_1": "linear-gradient(135deg,#f1f7ff,#e5f0ff)",
        "quick_2": "linear-gradient(135deg,#f7f1ff,#eee5ff)",
        "quick_3": "linear-gradient(135deg,#fff4f3,#ffebeb)",
        "quick_4": "linear-gradient(135deg,#effbf8,#e2f7f2)",
        "quick_5": "linear-gradient(135deg,#f7f2ff,#eee7ff)",
    }

# CSS variables are applied to the entire Streamlit window, not individual cards.
css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root {{
  --app-bg: {T['app_bg']};
  --app-bg-2: {T['app_bg_2']};
  --sidebar-bg: {T['sidebar_bg']};
  --panel: {T['panel']};
  --panel-alt: {T['panel_alt']};
  --panel-soft: {T['panel_soft']};
  --text: {T['text']};
  --text-soft: {T['text_soft']};
  --muted: {T['muted']};
  --border: {T['border']};
  --blue: {T['blue']};
  --blue-deep: {T['blue_deep']};
  --blue-soft: {T['blue_soft']};
  --green: {T['green']};
  --green-soft: {T['green_soft']};
  --warning-bg: {T['warning_bg']};
  --warning-border: {T['warning_border']};
  --warning-text: {T['warning_text']};
  --user-bubble: {T['user_bubble']};
  --assistant-bubble: {T['assistant_bubble']};
  --input-bg: {T['input_bg']};
  --shadow: {T['shadow']};
}}
html, body, [class*="css"], button, input, textarea {{
  font-family: 'Inter', sans-serif !important;
}}
.stApp {{
  background: linear-gradient(120deg,var(--app-bg),var(--app-bg-2) 58%,var(--app-bg));
  color: var(--text);
}}
[data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
  background: transparent !important;
  color: var(--text) !important;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stSidebar"] {{
  background: var(--sidebar-bg) !important;
  border-right: 1px solid var(--border);
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 1rem; }}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
[data-testid="stMainBlockContainer"] {{
  max-width: 1600px;
  padding-top: 1.35rem;
  padding-bottom: 7rem;
}}
.stMarkdown, .stMarkdown p, .stMarkdown li, label,
[data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] {{
  color: var(--text) !important;
}}
.brand {{
  display:flex; align-items:center; gap:12px;
  padding:4px 2px 18px; border-bottom:1px solid var(--border);
  margin-bottom:14px;
}}
.brand-shield {{
  width:55px;height:60px;border-radius:17px 17px 23px 23px;
  background:linear-gradient(145deg,#278df0,#0755b8);
  display:flex;align-items:center;justify-content:center;
  color:#fff !important;font-size:30px;font-weight:800;
  box-shadow:0 7px 18px rgba(15,92,190,.25);
}}
.brand-title {{font-size:17px;font-weight:800;line-height:1.15;color:var(--text) !important;}}
.brand-sub {{font-size:11px;color:var(--muted) !important;margin-top:5px;}}
.side-section {{font-size:13px;font-weight:800;color:var(--text) !important;padding:12px 4px 7px;}}
.side-note {{
  background:var(--green-soft);border:1px solid var(--border);color:var(--green) !important;
  border-radius:10px;padding:10px 11px;font-size:11px;font-weight:700;margin:9px 0 12px;
}}
.main-title {{font-size:clamp(25px,2.3vw,34px);font-weight:800;letter-spacing:-.8px;color:var(--text) !important;margin:0;}}
.main-subtitle {{font-size:14px;color:var(--text-soft) !important;margin-top:4px;line-height:1.5;}}
.warning {{
  background:var(--warning-bg);border:1px solid var(--warning-border);border-radius:11px;
  padding:9px 12px;color:var(--warning-text) !important;font-size:11px;margin:10px 0 14px;
}}
.hero-side {{
  min-height:102px;display:flex;align-items:center;justify-content:center;gap:10px;
  background:{T['hero_bg']};border:1px solid var(--border);border-radius:17px;padding:12px;
}}
.hero-shield {{font-size:47px;}}
.hero-copy {{font-size:15px;font-weight:800;line-height:1.25;color:var(--text) !important;}}
.hero-copy span {{font-size:11px;color:var(--blue) !important;font-weight:700;}}
.quick-card {{
  min-height:105px;border:1px solid var(--border);border-radius:14px;
  padding:12px 11px;background:var(--panel);box-shadow:0 3px 12px var(--shadow);
}}
.quick-card.q1 {{background:{T['quick_1']};}}
.quick-card.q2 {{background:{T['quick_2']};}}
.quick-card.q3 {{background:{T['quick_3']};}}
.quick-card.q4 {{background:{T['quick_4']};}}
.quick-card.q5 {{background:{T['quick_5']};}}
.quick-icon {{font-size:23px;margin-bottom:5px;}}
.quick-title {{font-size:12px;font-weight:800;color:var(--text) !important;line-height:1.3;}}
.quick-desc {{font-size:10px;color:var(--text-soft) !important;margin-top:5px;line-height:1.35;}}
.panel {{
  background:var(--panel);border:1px solid var(--border);border-radius:15px;
  padding:14px;box-shadow:0 4px 16px var(--shadow);margin-bottom:12px;
}}
.panel-title {{font-size:15px;font-weight:800;color:var(--text) !important;margin:2px 0 11px;}}
.summary-head {{background:var(--green-soft);color:var(--green) !important;border-radius:9px;padding:9px 11px;font-weight:800;margin-bottom:9px;font-size:13px;}}
.summary-row {{display:flex;justify-content:space-between;gap:8px;font-size:11px;padding:6px 2px;color:var(--text-soft) !important;border-bottom:1px solid var(--border);}}
.summary-row:last-child {{border-bottom:0;}}
.summary-row b {{color:var(--text) !important;}}
.pill {{display:inline-block;background:var(--blue-soft);color:var(--blue) !important;padding:4px 8px;border-radius:8px;font-size:10px;font-weight:700;}}
.source-card {{background:var(--panel-alt);border:1px solid var(--border);border-radius:10px;padding:10px;margin:8px 0;}}
.source-id {{font-size:11px;font-weight:800;color:var(--text) !important;}}
.source-name {{font-size:10px;color:var(--text-soft) !important;margin-top:3px;}}
.chat-heading {{font-size:15px;font-weight:800;color:var(--text) !important;margin:2px 0 10px;}}
.message-row {{display:flex;gap:10px;align-items:flex-start;margin:5px 0 15px;}}
.avatar {{width:36px;height:36px;min-width:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--blue-soft);color:var(--blue) !important;font-size:18px;}}
.bubble {{max-width:100%;background:var(--assistant-bubble);border:1px solid var(--border);border-radius:4px 14px 14px 14px;padding:12px 14px;color:var(--text) !important;font-size:13px;line-height:1.6;}}
.user-row {{display:flex;justify-content:flex-end;gap:9px;margin:12px 0 15px;}}
.user-bubble {{max-width:82%;background:var(--user-bubble);border:1px solid var(--border);border-radius:14px 4px 14px 14px;padding:11px 14px;color:var(--text) !important;font-size:13px;line-height:1.5;}}
.timestamp {{font-size:10px;color:var(--muted) !important;margin-top:4px;}}
.stButton > button {{
  border-radius:10px;border:1px solid var(--border);font-weight:650;
  color:var(--text) !important;background:var(--panel);min-height:38px;
  transition:all .15s ease;
}}
.stButton > button:hover {{border-color:var(--blue);color:var(--blue) !important;}}
.stButton > button[kind="primary"] {{background:linear-gradient(135deg,#176bd2,#0b4eae);color:#fff !important;border:0;}}
[data-testid="stChatInput"] {{
  position:relative !important;
  left:auto !important;
  right:auto !important;
  bottom:auto !important;
  width:100% !important;
  max-width:100% !important;
  margin:12px 0 0 !important;
  border:1.5px solid var(--blue) !important;
  border-radius:17px !important;
  background:var(--input-bg) !important;
  box-shadow:0 5px 16px var(--shadow) !important;
  box-sizing:border-box !important;
}}
[data-testid="stChatInput"] > div {{
  width:100% !important;
  max-width:100% !important;
}}
[data-testid="stChatInput"] textarea {{color:var(--text) !important;background:transparent !important;font-family:'Inter',sans-serif !important;}}
[data-testid="stChatInput"] textarea::placeholder {{color:var(--muted) !important;}}
[data-baseweb="select"] > div, [data-testid="stDateInput"] input,
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{
  background:var(--panel) !important;color:var(--text) !important;border-color:var(--border) !important;
}}
[data-baseweb="popover"], [data-baseweb="menu"] {{background:var(--panel) !important;color:var(--text) !important;}}
[data-baseweb="menu"] * {{color:var(--text) !important;}}
[data-testid="stVerticalBlockBorderWrapper"] {{border-color:var(--border) !important;background:var(--panel) !important;border-radius:14px !important;}}
[data-testid="stChatMessage"] {{background:var(--assistant-bubble) !important;border:1px solid var(--border);border-radius:14px;padding:12px 14px;margin:10px 0;}}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{color:var(--text) !important;}}
[data-testid="stExpander"] {{border-color:var(--border) !important;background:var(--panel) !important;border-radius:11px !important;}}
[data-testid="stAlert"] {{border-radius:11px;}}
hr {{border-color:var(--border) !important;}}
.footer {{font-size:10px;color:var(--muted) !important;text-align:center;padding:10px 0;line-height:1.8;}}
.small-muted {{font-size:10px;color:var(--muted) !important;}}
@media (max-width: 1050px) {{
  .main-title {{font-size:25px;}}
  .hero-side {{display:none;}}
}}
@media (max-width: 700px) {{
  [data-testid="stMainBlockContainer"] {{padding-left:1rem;padding-right:1rem;}}
  .quick-card {{min-height:95px;}}
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ============================================================
# API CONFIGURATION AND HELPERS
# ============================================================
API_BASE_URL = os.getenv(
    "POLICY_ADVISOR_API_BASE_URL",
    "http://localhost:8000",
).rstrip("/")

API_URL = f"{API_BASE_URL}/ask"
HEALTH_URL = f"{API_BASE_URL}/health"

API_TIMEOUT = int(
    os.getenv(
        "POLICY_ADVISOR_API_TIMEOUT",
        "90",
    )
)
API_TIMEOUT = int(os.getenv("POLICY_ADVISOR_API_TIMEOUT", "45"))
COMPARE_API_URL = os.getenv(
    "POLICY_ADVISOR_COMPARE_API_URL",
    "http://localhost:8000/compare",
)

def check_backend_health() -> bool:
    try:
        response = requests.get(
            HEALTH_URL,
            timeout=3,
        )

        return response.status_code == 200

    except requests.RequestException:
        return False
backend_online = check_backend_health()
if backend_online:
    st.success("FastAPI backend connected")
else:
    st.error("FastAPI backend unavailable")
def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)


def source_fields(source: Any):
    if isinstance(source, dict):
        source_id = (
            source.get("id")
            or source.get("clause_id")
            or source.get("document_id")
            or source.get("source_id")
            or "Policy source"
        )
        title = (
            source.get("title")
            or source.get("name")
            or source.get("section")
            or source.get("category")
            or "Policy clause"
        )
        return safe_text(source_id), safe_text(title)
    return safe_text(source), "Supporting policy source"

PLAN_ID_MAP = {
    "Silver Health Plan": "PLAN001",
    "Gold Health Plan": "PLAN002",
    "Platinum Health Plan": "PLAN003",
}
CATEGORY_MAP = {
    "Benefits": "benefit",
    "Waiting Periods": "waiting_period",
    "Exclusions": "exclusion",
    "Required Documents": "documentation",
}
def call_advisor_api(
    question: str,
    plan: str,
    version: str,
) -> Dict[str, Any]:

    plan_id = PLAN_ID_MAP.get(plan)

    if not plan_id:
        raise ValueError(
            f"No backend plan ID configured for: {plan}"
        )

    policy_version = version.split(" ")[0]

    payload = {
        "question": question,
        "plan_id": plan_id,
        "version": policy_version,
    }

    response = requests.post(
        API_URL,
        json=payload,
        timeout=API_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    answer = data.get("answer")

    if not answer:
        raise ValueError(
            "FastAPI returned no answer."
        )

    sources = (
        data.get("source_clauses")
        or data.get("sources")
        or data.get("citations")
        or []
    )

    if isinstance(sources, dict):
        sources = [sources]

    if not isinstance(sources, list):
        sources = []

    intent = safe_text(
        data.get("intent"),
        "Policy question",
    )

    confidence = data.get(
        "confidence"
    )

    returned_plan_id = safe_text(
        data.get("plan_id"),
        plan_id,
    )

    returned_version = safe_text(
        data.get("version"),
        policy_version,
    )

    answer_lower = safe_text(
        answer
    ).lower()

    if sources:
        status = "Grounded response"

    elif (
        intent == "escalation"
        or "human review" in answer_lower
        or "cannot guarantee" in answer_lower
    ):
        status = "Human review required"

    else:
        status = "Guarded response"

    return {
        "answer": safe_text(answer),
        "sources": sources,
        "topic": intent,
        "intent": intent,
        "confidence": confidence,
        "plan_id": returned_plan_id,
        "version": returned_version,
        "status": status,
        "raw": data,
    }

def call_comparison_api(
    question: str,
    plan_a: str,
    version_a: str,
    plan_b: str,
    version_b: str,
    category: str,
) -> Dict[str, Any]:
    """
    Call FastAPI POST /compare.
    """

    plan_a_id = PLAN_ID_MAP[plan_a]
    plan_b_id = PLAN_ID_MAP[plan_b]

    version_a_value = version_a.split(" ")[0]
    version_b_value = version_b.split(" ")[0]

    category_value = CATEGORY_MAP[category]

    payload = {
        "question": question,
        "plan_a_id": plan_a_id,
        "plan_a_version": version_a_value,
        "plan_b_id": plan_b_id,
        "plan_b_version": version_b_value,
        "category": category_value,
        "top": 3,
    }

    response = requests.post(
        COMPARE_API_URL,
        json=payload,
        timeout=API_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    return {
    "answer": safe_text(
        data.get("answer")
    ),

    "summary": safe_text(
        data.get("summary")
    ),

    "comparison_rows": (
        data.get("comparison_rows")
        or []
    ),

    "plan_a_id": safe_text(
        data.get("plan_a_id")
    ),

    "plan_a_version": safe_text(
        data.get("plan_a_version")
    ),

    "plan_b_id": safe_text(
        data.get("plan_b_id")
    ),

    "plan_b_version": safe_text(
        data.get("plan_b_version")
    ),

    "sources_a": (
        data.get("sources_a")
        or []
    ),

    "sources_b": (
        data.get("sources_b")
        or []
    ),

    "status": safe_text(
        data.get("status")
    ),
}
def ask_advisor(
    question: str,
    plan: str,
    version: str,
) -> None:

    question = question.strip()

    if not question:
        return

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
            "timestamp": datetime.now().strftime(
                "%I:%M %p"
            ),
        }
    )

    try:

        result = call_advisor_api(
            question,
            plan,
            version,
        )

        st.session_state.api_error = ""

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
                "topic": result["topic"],
                "intent": result["intent"],
                "confidence": result[
                    "confidence"
                ],
                "plan_id": result[
                    "plan_id"
                ],
                "version": result[
                    "version"
                ],
                "status": result["status"],
                "timestamp": (
                    datetime.now().strftime(
                        "%I:%M %p"
                    )
                ),
            }
        )

        st.session_state.last_answer = (
            result
        )

    except requests.Timeout:

        st.session_state.api_error = (
            "FastAPI request timed out."
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "The policy advisor took too "
                    "long to respond. Please try "
                    "again."
                ),
                "sources": [],
                "topic": "System",
                "intent": "system_error",
                "confidence": None,
                "plan_id": None,
                "version": None,
                "status": "Backend timeout",
                "timestamp": (
                    datetime.now().strftime(
                        "%I:%M %p"
                    )
                ),
            }
        )

    except requests.ConnectionError as exc:

        st.session_state.api_error = str(
            exc
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "The policy advisor backend "
                    "is currently unavailable."
                ),
                "sources": [],
                "topic": "System",
                "intent": "system_error",
                "confidence": None,
                "plan_id": None,
                "version": None,
                "status": (
                    "Backend unavailable"
                ),
                "timestamp": (
                    datetime.now().strftime(
                        "%I:%M %p"
                    )
                ),
            }
        )

    except requests.HTTPError as exc:

        details = ""

        if exc.response is not None:
            details = exc.response.text

        st.session_state.api_error = (
            f"{exc} | {details}"
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "The backend could not "
                    "process this policy request."
                ),
                "sources": [],
                "topic": "System",
                "intent": "system_error",
                "confidence": None,
                "plan_id": None,
                "version": None,
                "status": "Request failed",
                "timestamp": (
                    datetime.now().strftime(
                        "%I:%M %p"
                    )
                ),
            }
        )

    except (
        ValueError,
        TypeError,
        KeyError,
    ) as exc:

        st.session_state.api_error = str(
            exc
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "The backend returned an "
                    "unexpected response."
                ),
                "sources": [],
                "topic": "System",
                "intent": "system_error",
                "confidence": None,
                "plan_id": None,
                "version": None,
                "status": (
                    "Invalid API response"
                ),
                "timestamp": (
                    datetime.now().strftime(
                        "%I:%M %p"
                    )
                ),
            }
        )

def get_policy_documents():
    """Get available policy documents from the backend."""

    try:
        response = requests.get(
            f"{API_BASE_URL}/policy-documents",
            timeout=30,
        )

        response.raise_for_status()

        return response.json().get("documents", [])

    except requests.RequestException as exc:
        st.error(f"Unable to load policy documents: {exc}")
        return []

def get_policy_document(filename: str):
    """Retrieve a policy PDF from the backend."""

    try:
        response = requests.get(
            f"{API_BASE_URL}/policy-documents/{filename}",
            timeout=30,
        )

        response.raise_for_status()

        return response.content

    except requests.RequestException as exc:
        st.error(f"Unable to load policy document: {exc}")
        return None

def get_policy_document(filename: str):
    """Retrieve a policy PDF from the backend."""

    try:
        encoded_filename = quote(filename, safe="")

        response = requests.get(
            f"{API_BASE_URL}/policy-documents/{encoded_filename}",
            timeout=30,
        )

        response.raise_for_status()

        return response.content

    except requests.RequestException as exc:
        st.error(f"Unable to load policy document: {exc}")
        return None

documents = get_policy_documents()

def display_pdf(pdf_bytes: bytes):
    """Display a PDF document inside Streamlit."""

    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="700"
            type="application/pdf">
        </iframe>
    """

    st.markdown(
        pdf_display,
        unsafe_allow_html=True,
    )

# ============================================================
# SIDEBAR — NAVIGATION, POLICY SELECTION AND GLOBAL THEME
# ============================================================
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

    st.markdown("<div class='side-section'>WORKSPACE</div>", unsafe_allow_html=True)
    nav_items = [
        "💬  Chat with Advisor",
        "⚖️  Compare Plans",
        "▤  Policy Versions",
        "◷  My Conversations",
        "⇧  Upload Policy",
        "ⓘ  Help & FAQs",
    ]
    selected_nav = st.radio(
        "Navigation",
        nav_items,
        index=0,
        label_visibility="collapsed",
        key="main_navigation",
    )

    st.markdown("---")
    st.markdown("<div class='side-section'>SELECT YOUR POLICY</div>", unsafe_allow_html=True)
    plan = st.selectbox(
        "Insurance plan",
        ["Silver Health Plan", "Gold Health Plan", "Platinum Health Plan"],
        index=0,
        label_visibility="collapsed",
        key="selected_plan",
    )
    version = st.selectbox(
        "Policy version",
        ["v2 (Active)", "v1 (Archived)"],
        index=0,
        label_visibility="collapsed",
        key="selected_version",
    )
    st.date_input(
        "Effective date",
        value=date(2025, 1, 1),
        disabled=True,
    )

    st.markdown(
        f"<div class='side-note'>✓ &nbsp; {html.escape(plan)} · {html.escape(version)}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("<div class='side-section'>APPEARANCE</div>", unsafe_allow_html=True)
    # This single control changes the CSS variables for the entire app window.
    st.toggle("Dark mode", key="dark_mode", help="Switch the complete application between light and dark themes.")
    st.caption("Theme applies to the full window and sidebar.")

    st.markdown("---")
    if st.button("＋  New Conversation", use_container_width=True, type="primary"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! Ask me anything about your selected policy.",
                "sources": [],
                "topic": "Getting started",
                "status": "Ready",
                "timestamp": datetime.now().strftime("%I:%M %p"),
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
        "<div class='footer'>✦ Powered by Microsoft Azure<br>Privacy · Terms · Help</div>",
        unsafe_allow_html=True,
    )
if selected_nav == "⚖️  Compare Plans":

    st.markdown(
        "<div class='main-title'>Compare Health Plans</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='main-subtitle'>
        Compare two fictional health insurance plans
        using grounded policy evidence.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='warning'>
        ⚠️ Comparisons are based only on retrieved
        policy clauses. They do not guarantee claim
        or coverage approval.
        </div>
        """,
        unsafe_allow_html=True,
    )

    plan_a_col, vs_col, plan_b_col = st.columns(
        [1, 0.2, 1],
        vertical_alignment="center",
    )


    # --------------------------------------------
    # Plan A
    # --------------------------------------------

    with plan_a_col:

        st.markdown("### Plan A")

        compare_plan_a = st.selectbox(
            "Select first plan",
            list(PLAN_ID_MAP.keys()),
            index=0,
            key="compare_plan_a",
        )

        compare_version_a = st.selectbox(
            "Version",
            [
                "v2 (Active)",
                "v1 (Archived)",
            ],
            index=1,
            key="compare_version_a",
        )


    # --------------------------------------------
    # VS
    # --------------------------------------------

    with vs_col:

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:22px;
                font-weight:800;
                padding-top:35px;
            ">
                VS
            </div>
            """,
            unsafe_allow_html=True,
        )


    # --------------------------------------------
    # Plan B
    # --------------------------------------------

    with plan_b_col:

        st.markdown("### Plan B")

        compare_plan_b = st.selectbox(
            "Select second plan",
            list(PLAN_ID_MAP.keys()),
            index=1,
            key="compare_plan_b",
        )

        compare_version_b = st.selectbox(
            "Version",
            [
                "v2 (Active)",
                "v1 (Archived)",
            ],
            index=1,
            key="compare_version_b",
        )


    # --------------------------------------------
    # Category
    # --------------------------------------------

    compare_category = st.selectbox(
        "What would you like to compare?",
        list(CATEGORY_MAP.keys()),
        index=0,
        key="compare_category",
    )


    # --------------------------------------------
    # Build question
    # --------------------------------------------

    comparison_question = (
        f"Compare the {compare_category.lower()} "
        f"of {compare_plan_a} and "
        f"{compare_plan_b}."
    )


    # --------------------------------------------
    # Compare button
    # --------------------------------------------

    if st.button(
        "⚖️ Compare Plans",
        type="primary",
        use_container_width=True,
    ):

        if (
            compare_plan_a == compare_plan_b
            and compare_version_a
            == compare_version_b
        ):

            st.warning(
                "Please select two different "
                "policies for comparison."
            )

        else:

            try:

                with st.spinner(
                    "Retrieving policy evidence "
                    "and comparing plans..."
                ):

                    comparison_result = (
                        call_comparison_api(
                            question=(
                                comparison_question
                            ),
                            plan_a=(
                                compare_plan_a
                            ),
                            version_a=(
                                compare_version_a
                            ),
                            plan_b=(
                                compare_plan_b
                            ),
                            version_b=(
                                compare_version_b
                            ),
                            category=(
                                compare_category
                            ),
                        )
                    )

                st.session_state[
                    "comparison_result"
                ] = comparison_result

            except requests.RequestException as exc:

                st.error(
                    "The comparison service "
                    "could not be reached."
                )

                st.session_state.api_error = str(
                    exc
                )


    # --------------------------------------------
    # Display result
    # --------------------------------------------

    result = st.session_state.get(
        "comparison_result"
    )

    if result:

        st.markdown("---")

        st.markdown(
            "## 📊 Policy Comparison"
        )

        # ==========================================
        # TABULAR COMPARISON
        # ==========================================

        rows = result.get(
            "comparison_rows",
            []
        )

        if rows:

            table_data = []

            for row in rows:

                table_data.append(
                    {
                        "Feature": row.get(
                            "feature",
                            ""
                        ),

                        compare_plan_a: row.get(
                            "plan_a",
                            ""
                        ),

                        compare_plan_b: row.get(
                            "plan_b",
                            ""
                        ),

                        "Difference": row.get(
                            "difference",
                            ""
                        ),
                    }
                )

            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.warning(
                "No structured comparison "
                "rows were returned."
            )

        # ==========================================
        # KEY TAKEAWAY
        # ==========================================

        summary = result.get(
            "summary",
            ""
        )

        if summary:

            st.markdown(
                "### 💡 Key Takeaway"
            )

            st.info(
                summary
            )

        # ==========================================
        # STATUS
        # ==========================================

        status = result.get(
            "status",
            ""
        )

        if status:

            st.caption(
                f"Status: {status}"
            )

        # ==========================================
        # SUPPORTING SOURCES
        # ==========================================

        st.markdown(
            "### 📚 Supporting Policy Evidence"
        )

        source_a_col, source_b_col = (
            st.columns(2)
        )

        # ------------------------------------------
        # PLAN A
        # ------------------------------------------

        with source_a_col:

            st.markdown(
                f"### {compare_plan_a}"
            )

            st.write(
                "**Plan ID:**",
                result.get(
                    "plan_a_id",
                    ""
                ),
            )

            st.write(
                "**Version:**",
                result.get(
                    "plan_a_version",
                    ""
                ),
            )

            st.markdown(
                "#### Supporting Clauses"
            )

            sources_a = result.get(
                "sources_a",
                []
            )

            if sources_a:

                for clause_id in sources_a:

                    st.success(
                        f"📄 {clause_id}"
                    )

            else:

                st.caption(
                    "No supporting clauses "
                    "were returned."
                )

        # ------------------------------------------
        # PLAN B
        # ------------------------------------------

        with source_b_col:

            st.markdown(
                f"### {compare_plan_b}"
            )

            st.write(
                "**Plan ID:**",
                result.get(
                    "plan_b_id",
                    ""
                ),
            )

            st.write(
                "**Version:**",
                result.get(
                    "plan_b_version",
                    ""
                ),
            )

            st.markdown(
                "#### Supporting Clauses"
            )

            sources_b = result.get(
                "sources_b",
                []
            )

            if sources_b:

                for clause_id in sources_b:

                    st.success(
                        f"📄 {clause_id}"
                    )

            else:

                st.caption(
                    "No supporting clauses "
                    "were returned."
                )

    else:

        st.info(
            "Select two plans and click "
            "'Compare Plans' to generate "
            "a grounded comparison."
        )


    # Prevent normal Chat UI from rendering
    # while Compare Plans page is selected.
    st.stop()
# ============================================================
# HEADER / HERO
# ============================================================
header_left, header_right = st.columns([5, 1.35], vertical_alignment="center")
with header_left:
    st.markdown(
        "<div class='main-title'>Health Insurance Policy Advisor</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='main-subtitle'>Understand your benefits, waiting periods, exclusions and more — powered by AI.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='warning'>⚠️ &nbsp; Educational policy assistant. It does not guarantee claim approval or provide medical advice.</div>",
        unsafe_allow_html=True,
    )
with header_right:
    st.markdown(
        """
        <div class="hero-side">
          <div class="hero-shield">🛡️</div>
          <div class="hero-copy">Better Information<br><span>Healthier Tomorrow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# QUICK ACTIONS
# ============================================================
quick_actions = [
    ("🛡️", "Check Benefits", "What's covered in my plan?", "What benefits are covered under my selected plan?"),
    ("◷", "Waiting Periods", "When can I claim certain benefits?", "What are the waiting periods in my selected plan?"),
    ("🚫", "Exclusions", "What is not covered?", "What exclusions should I know about in my selected plan?"),
    ("▤", "Required Documents", "What documents do I need?", "What documents are required to make a claim?"),
    ("⚖️", "Compare Plans", "See side-by-side benefits", "Compare the benefits of Silver and Gold plans."),
]
quick_columns = st.columns(5, gap="small")
for index, (icon, title, description, prompt) in enumerate(quick_actions):
    with quick_columns[index]:
        st.markdown(
            f"""
            <div class="quick-card q{index + 1}">
              <div class="quick-icon">{icon}</div>
              <div class="quick-title">{html.escape(title)} &nbsp; →</div>
              <div class="quick-desc">{html.escape(description)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Ask", key=f"quick_action_{index}", use_container_width=True):
            ask_advisor(prompt, plan, version)
            st.rerun()

st.write("")
st.subheader("📄 Policy Documents")

documents = get_policy_documents()

if documents:

    selected_document = st.selectbox(
        "Select a policy document",
        documents,
        format_func=lambda path: path.split("/")[-1]
    )

    if selected_document:

        if st.button("View Policy Document"):

            pdf_bytes = get_policy_document(selected_document)

            if pdf_bytes:

                st.session_state["policy_pdf"] = pdf_bytes
                st.session_state["policy_pdf_name"] = selected_document


    if "policy_pdf" in st.session_state:

        display_pdf(
            st.session_state["policy_pdf"]
        )

        filename = st.session_state[
            "policy_pdf_name"
        ].split("/")[-1]

        st.download_button(
            label="⬇️ Download Policy Document",
            data=st.session_state["policy_pdf"],
            file_name=filename,
            mime="application/pdf",
        )

else:

    st.info(
        "No policy documents are currently available."
    )

# ============================================================
# MAIN CONVERSATION + RIGHT INFORMATION RAIL
# ============================================================
chat_col, rail_col = st.columns([2.25, 1], gap="medium")

with chat_col:
    # One bordered conversation card contains its heading, scrollable history,
    # and the question composer. This keeps the composer the same width as
    # Policy Conversation instead of stretching across the whole browser.
    with st.container(border=True):

        heading_col, clear_col = st.columns([4, 1], vertical_alignment="center")
        with heading_col:
            st.markdown(
                "<div class='chat-heading'>💬 Policy Conversation</div>",
                unsafe_allow_html=True
            )
        with clear_col:
            if st.button(
                "🗑 Clear Chat",
                key="clear_chat_main",
                use_container_width=True
            ):
                st.session_state.messages = []
                st.session_state.last_answer = None
                st.rerun()

        # Only the conversation history scrolls.
        with st.container(height=430, border=False):
            if not st.session_state.messages:
                st.info(
                    "Your conversation is clear. Ask a question below "
                    "or choose a quick action above."
                )

            for message in st.session_state.messages:
                role = message.get("role", "assistant")
                timestamp = message.get("timestamp", "")
                avatar = "👤" if role == "user" else "🤖"

                with st.chat_message(role, avatar=avatar):
                    st.markdown(safe_text(message.get("content", "")))

                    if timestamp:
                        st.caption(timestamp)

                    if role == "assistant":
                        status = message.get("status", "")
                        if status and status != "Ready":
                            st.caption(f"Answer status: {status}")

                        message_sources = message.get("sources", []) or []
                        if message_sources:
                            with st.expander(
                                f"📚 View supporting clauses ({len(message_sources)})",
                                expanded=False
                            ):
                                for source in message_sources:
                                    source_id, source_title = source_fields(source)
                                    st.markdown(f"**{source_id}** — {source_title}")

        # IMPORTANT: Keep st.chat_input inside chat_col and inside the
        # bordered conversation card. It will use this column's width.
        question = st.chat_input(
            "Ask anything about your health insurance policy...",
            key="policy_conversation_input"
        )

        if question:
            ask_advisor(question, plan, version)
            st.rerun()

with rail_col:
    latest_assistant = next(
        (
            message for message in reversed(st.session_state.messages)
            if message.get("role") == "assistant" and message.get("status") != "Ready"
        ),
        None,
    )
    topic = latest_assistant.get("topic", "Not selected") if latest_assistant else "Not selected"
    status = latest_assistant.get("status", "Waiting for a question") if latest_assistant else "Waiting for a question"
    latest_sources = latest_assistant.get("sources", []) if latest_assistant else []

    st.markdown(
        f"""
        <div class="panel">
          <div class="summary-head">◉ &nbsp; Current Context</div>
          <div class="summary-row"><b>Plan</b><span class="pill">{html.escape(plan)}</span></div>
          <div class="summary-row"><b>Version</b><span class="pill">{html.escape(version)}</span></div>
          <div class="summary-row"><b>Topic</b><span>{html.escape(topic)}</span></div>
          <div class="summary-row"><b>Answer Status</b><span>{html.escape(status)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("#### 📄 Sources Used")
        if latest_sources:
            for source in latest_sources[:5]:
                source_id, source_title = source_fields(source)
                st.markdown(
                    f"<div class='source-card'><div class='source-id'>📄 {html.escape(source_id)}</div>"
                    f"<div class='source-name'>{html.escape(source_title)}</div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Supporting policy clauses will appear here when returned by the API.")

    with st.container(border=True):
        st.markdown("#### ✨ Related Questions")
        related_questions = [
            f"What are the waiting periods in the {plan.replace(' Health Plan', '')} plan?",
            f"What exclusions apply to the {plan.replace(' Health Plan', '')} plan?",
            "Which documents are needed for a hospitalisation claim?",
        ]
        for index, related_question in enumerate(related_questions):
            if st.button(related_question, key=f"related_question_{index}", use_container_width=True):
                ask_advisor(related_question, plan, version)
                st.rerun()

# ============================================================
# BACKEND STATUS / SETTINGS
# ============================================================
with st.expander("⚙️ Backend connection details"):
    st.write(f"FastAPI endpoint: `{API_URL}`")
    st.caption("Set POLICY_ADVISOR_API_URL if your FastAPI endpoint is hosted somewhere other than localhost:8000.")
    if st.session_state.api_error:
        st.warning(f"Latest API connection issue: {st.session_state.api_error}")
    else:
        st.success("No API connection error has been recorded in this session.")

# Chat input is intentionally rendered inside the Policy Conversation
# card above, not at the root level of the page.
