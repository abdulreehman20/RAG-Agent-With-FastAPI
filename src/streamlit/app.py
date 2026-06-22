"""FastAPI RAG Agent — Streamlit UI."""

from __future__ import annotations

import streamlit as st

from api_client import ApiError, get_me, ingest_url, login, query_rag, signup
from config import API_BASE_URL

st.set_page_config(
    page_title="FastAPI RAG Agent",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
_AUTH_CSS = """
<style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stAppViewContainer"] .main .block-container {
        max-width: 100%;
        padding-top: 6vh;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .auth-header {
        text-align: center;
        margin-bottom: 0.25rem;
    }
    .auth-header h1 {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .auth-header p {
        color: rgba(250, 250, 250, 0.65);
        font-size: 0.95rem;
        margin: 0;
    }
    [data-testid="stForm"] {
        border: 1px solid rgba(250, 250, 250, 0.14);
        border-radius: 14px;
        padding: 1.25rem 1.5rem 0.75rem;
        background: rgba(255, 255, 255, 0.04);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
    }
    [data-testid="stTabs"] { margin-top: 0.5rem; }
</style>
"""

_CHAT_CSS = """
<style>
    [data-testid="stAppViewContainer"] .main .block-container {
        max-width: 100% !important;
        padding-top: 1rem;
        padding-bottom: 7rem;
        padding-left: 1.25rem;
        padding-right: 1.5rem;
    }
    [data-testid="stChatMessage"] {
        width: 100%;
        max-width: 100%;
        margin-left: 0;
        margin-right: 0;
    }
    [data-testid="stChatMessageContent"] {
        text-align: left;
    }
    .chat-welcome {
        text-align: left;
        padding: 1.5rem 0 2rem;
        max-width: 48rem;
    }
    .chat-welcome h2 {
        font-size: 1.6rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .chat-welcome p {
        color: rgba(250, 250, 250, 0.65);
        font-size: 0.95rem;
        margin: 0;
    }
</style>
"""

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
_DEFAULTS: dict[str, object] = {
    "access_token": None,
    "user": None,
    "messages": [],
    "last_ingest": None,
    "pending_prompt": None,
}


def _init_session() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _logout() -> None:
    for key, value in _DEFAULTS.items():
        st.session_state[key] = value if not isinstance(value, list) else []


def _restore_session() -> bool:
    """Validate stored token via GET /auth/me."""
    token = st.session_state.access_token
    if not token:
        return False
    try:
        st.session_state.user = get_me(token)
        return True
    except ApiError:
        _logout()
        return False


# ---------------------------------------------------------------------------
# Auth UI (centered ~40% width)
# ---------------------------------------------------------------------------
def _render_auth() -> None:
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)

    # ~40% centered column (3 : 4 : 3)
    left, center, right = st.columns([3, 4, 3], gap="large")

    with center:
        st.markdown(
            """
            <div class="auth-header">
                <h1>FastAPI RAG Agent</h1>
                <p>Log in or create an account to ingest URLs and chat with your documents.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

        with login_tab:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button(
                    "Log in", type="primary", use_container_width=True
                )

            if submitted:
                if not email or not password:
                    st.error("Email and password are required.")
                else:
                    try:
                        token_data = login(email.strip(), password)
                        st.session_state.access_token = token_data["access_token"]
                        st.session_state.user = get_me(st.session_state.access_token)
                        st.session_state.messages = []
                        st.success("Logged in successfully.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))

        with signup_tab:
            with st.form("signup_form", clear_on_submit=False):
                full_name = st.text_input("Full name (optional)", key="signup_name")
                email = st.text_input("Email", key="signup_email")
                password = st.text_input(
                    "Password (min 8 characters)",
                    type="password",
                    key="signup_password",
                )
                submitted = st.form_submit_button(
                    "Create account", type="primary", use_container_width=True
                )

            if submitted:
                if not email or not password:
                    st.error("Email and password are required.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    try:
                        signup(email.strip(), password, full_name.strip() or None)
                        st.success("Account created. Log in with your credentials.")
                    except ApiError as exc:
                        st.error(str(exc))


# ---------------------------------------------------------------------------
# Post-login: sidebar + Claude-style chat
# ---------------------------------------------------------------------------
def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Account")
        user = st.session_state.user or {}
        display_name = user.get("full_name") or user.get("email", "unknown")
        st.markdown(f"**Signed in as**  \n{display_name}")
        if user.get("full_name"):
            st.caption(user.get("email", ""))

        if st.button("Log out", use_container_width=True):
            _logout()
            st.rerun()

        st.divider()
        st.markdown("### Ingest website")
        st.caption("Paste a URL to scrape, chunk, embed, and store in Qdrant.")

        url = st.text_input(
            "Website URL",
            placeholder="https://example.com/blog/article",
            key="ingest_url_input",
            label_visibility="collapsed",
        )

        if st.button("Ingest URL", type="primary", use_container_width=True):
            if not url.strip():
                st.warning("Enter a URL first.")
            else:
                with st.spinner("Ingesting… this may take a few minutes."):
                    try:
                        result = ingest_url(url.strip(), token=st.session_state.access_token)
                        st.session_state.last_ingest = result
                        st.success(
                            f"Saved **{result['chunks_saved']}** chunks to "
                            f"`{result['collection']}`."
                        )
                    except ApiError as exc:
                        st.error(str(exc))

        if st.session_state.last_ingest:
            ingest = st.session_state.last_ingest
            st.markdown("**Last ingestion**")
            st.caption(f"URL: {ingest.get('url', '')}")
            st.caption(
                f"{ingest.get('chunks_saved', 0)} chunks → `{ingest.get('collection', '')}`"
            )

        st.divider()
        st.caption(f"API: `{API_BASE_URL}`")


def _render_chat() -> None:
    st.markdown(_CHAT_CSS, unsafe_allow_html=True)

    if not st.session_state.messages and not st.session_state.pending_prompt:
        st.markdown(
            """
            <div class="chat-welcome">
                <h2>How can I help you today?</h2>
                <p>Ingest a URL in the sidebar, then ask questions about that content here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        with st.chat_message("assistant"):
            with st.spinner(""):
                try:
                    result = query_rag(prompt, token=st.session_state.access_token)
                    answer = result["answer"]
                    st.markdown(answer)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                except ApiError as exc:
                    st.error(str(exc))

    if prompt := st.chat_input("Message FastAPI RAG Agent…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_prompt = prompt
        st.rerun()


def _render_app() -> None:
    _render_sidebar()
    _render_chat()


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
def main() -> None:
    _init_session()

    if st.session_state.access_token and st.session_state.user is None:
        if not _restore_session():
            st.warning("Your session expired. Please log in again.")

    if st.session_state.access_token and st.session_state.user:
        _render_app()
    else:
        _render_auth()


main()
