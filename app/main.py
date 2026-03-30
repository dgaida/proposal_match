import streamlit as st
import os
import json
import threading
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from app.services.llm_service import LLMService
from app.utils.db_manager import DBManager
from app.utils.vector_store import VectorStore
from app.utils.translations import translate
from app.utils.geo_utils import batch_geocode

# UI Components
from app.ui.tabs import render_summarization_tab
from app.ui.tabs_content import (
    render_fit_tab,
    render_indexing_tab,
    render_matching_tab,
    render_linkedin_tab,
    render_database_tab,
)

# Load credentials from secrets.env if it exists
load_dotenv("secrets.env")

# Language Selection in Session State
if "lang" not in st.session_state:
    st.session_state.lang = "de"

# Page Configuration
st.set_page_config(
    page_title=translate("page_title", st.session_state.lang), layout="wide"
)

# Persistent Storage Initialization
if "db_manager" not in st.session_state:
    st.session_state.db_manager = DBManager()

    # Start background geocoding once per session
    if "geocoding_started" not in st.session_state:
        all_companies = st.session_state.db_manager.get_all_companies()
        nrw_variants = ["nrw", "nordrhein-westfalen", "north rhine-westphalia"]

        def is_nrw(c):
            state = getattr(c, "state", None) or (
                c.get("State") if isinstance(c, dict) else None
            )
            return (state or "").lower() in nrw_variants

        nrw_companies = [c for c in all_companies if is_nrw(c)]
        thread = threading.Thread(
            target=batch_geocode, args=(nrw_companies,), daemon=True
        )
        thread.start()
        st.session_state.geocoding_started = True

if "vector_store" not in st.session_state:
    st.session_state.vector_store = VectorStore()

# Load User Skills/Context
if "user_context" not in st.session_state:
    user_skill_path = "user_skill.md"
    if os.path.exists(user_skill_path):
        with open(user_skill_path, "r", encoding="utf-8") as f:
            st.session_state.user_context = f.read()
    else:
        st.session_state.user_context = ""


# LLM Service Initialization
def get_llm_service() -> Optional[LLMService]:
    """Initializes the LLM service based on sidebar configuration."""
    providers = ["openai", "groq", "gemini", "ollama"]
    env_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    default_index = providers.index(env_provider) if env_provider in providers else 0

    provider = st.sidebar.selectbox(
        translate("llm_provider", st.session_state.lang),
        providers,
        index=default_index,
        help=translate("llm_help", st.session_state.lang),
    )

    default_api_key = os.getenv(f"{provider.upper()}_API_KEY", "")
    api_key = st.sidebar.text_input(
        f"{provider.capitalize()} {translate('api_key', st.session_state.lang)}",
        value=default_api_key,
        type="password",
        help=translate(
            "api_key_help", st.session_state.lang, provider=provider.capitalize()
        ),
    )
    model = st.sidebar.text_input(
        translate("model_optional", st.session_state.lang),
        value=os.getenv("LLM_MODEL", ""),
        placeholder="e.g. gpt-4o, llama3-70b-8192",
        help=translate("model_help", st.session_state.lang),
    )

    if api_key or provider == "ollama":
        return LLMService(
            provider=provider, api_key=api_key, llm_model=model if model else None
        )
    return None


llm_service = get_llm_service()

# Language Switcher at the very top right
col_empty, col_lang = st.columns([8, 2])
with col_lang:
    lang_options = {"Deutsch": "de", "English": "en"}
    selected_lang_name = st.radio(
        "Language / Sprache",
        options=list(lang_options.keys()),
        index=0 if st.session_state.lang == "de" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    if lang_options[selected_lang_name] != st.session_state.lang:
        st.session_state.lang = lang_options[selected_lang_name]
        st.rerun()

# Sidebar - Settings
st.sidebar.title(translate("settings", st.session_state.lang))
fit_username = st.sidebar.text_input(
    translate("fit_username", st.session_state.lang),
    value=os.getenv("FIT_USERNAME", ""),
)
fit_password = st.sidebar.text_input(
    translate("fit_password", st.session_state.lang),
    value=os.getenv("FIT_PASSWORD", ""),
    type="password",
)
li_username = st.sidebar.text_input(
    translate("linkedin_username", st.session_state.lang),
    value=os.getenv("LINKEDIN_USERNAME", ""),
)
li_password = st.sidebar.text_input(
    translate("linkedin_password", st.session_state.lang),
    value=os.getenv("LINKEDIN_PASSWORD", ""),
    type="password",
)

# Main Header
st.title(translate("app_title", st.session_state.lang))

if not llm_service:
    st.warning(translate("configure_llm_warning", st.session_state.lang))
    st.stop()

# Tab Layout
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        translate("tab_summarization", st.session_state.lang),
        translate("tab_fit", st.session_state.lang),
        translate("tab_indexing", st.session_state.lang),
        translate("tab_matching", st.session_state.lang),
        translate("tab_linkedin", st.session_state.lang),
        translate("tab_database", st.session_state.lang),
    ]
)

# Initialize FIT cache in session state
if "fit_results" not in st.session_state:
    fit_cache_path = "data/fit_cache.json"
    if os.path.exists(fit_cache_path):
        try:
            with open(fit_cache_path, "r", encoding="utf-8") as f:
                st.session_state.fit_results = json.load(f)
        except Exception:
            st.session_state.fit_results = None
    else:
        st.session_state.fit_results = None


def parse_md_to_result(content: str) -> Dict[str, Any]:
    """Parses metadata from .md summaries for matching service compatibility."""
    result = {}
    lines = content.split("\n")
    for line in lines:
        if line.startswith("Zusammenfassung der Ausschreibung: "):
            result["Thema"] = line.replace(
                "Zusammenfassung der Ausschreibung: ", ""
            ).strip()
        elif line.startswith("Link: "):
            result["Link"] = line.replace("Link: ", "").strip()
        elif line.startswith("- Thema: "):
            result["Thema"] = line.replace("- Thema: ", "").strip()
        elif line.startswith("- Zielsetzung: "):
            result["Zielsetzung"] = line.replace("- Zielsetzung: ", "").strip()
        elif line.startswith("- Deadline: "):
            result["Deadline"] = line.replace("- Deadline: ", "").strip()
        elif line.startswith("- Budget: "):
            result["Budget"] = line.replace("- Budget: ", "").strip()
        elif line.startswith("- Laufzeit: "):
            result["Laufzeit"] = line.replace("- Laufzeit: ", "").strip()
        elif line.startswith("- Prozess: "):
            result["Einstufig_Zweistufig"] = line.replace("- Prozess: ", "").strip()
        elif line.startswith("- Partner: "):
            result["Anzahl_Projektpartner"] = line.replace("- Partner: ", "").strip()
        elif line.startswith("- Antragsberechtigt: "):
            result["Antragsberechtigt"] = line.replace(
                "- Antragsberechtigt: ", ""
            ).strip()
        elif line.startswith("- Antragsberechtigt_Details: "):
            result["Antragsberechtigt_Details"] = line.replace(
                "- Antragsberechtigt_Details: ", ""
            ).strip()
        elif line.startswith("- Sitz der Organisation: "):
            result["Sitz_der_Organisation"] = line.replace(
                "- Sitz der Organisation: ", ""
            ).strip()

    try:
        desc_start = content.find("Link:")
        desc_start = content.find("\n", desc_start) + 1
        desc_end = content.find("### Metadaten")
        result["Beschreibung"] = content[desc_start:desc_end].strip()
    except Exception:
        result["Beschreibung"] = "No description found."
    return result


with tab1:
    render_summarization_tab(llm_service, "data/summaries", parse_md_to_result)
with tab2:
    render_fit_tab(llm_service, fit_username, fit_password)
with tab3:
    render_indexing_tab(
        llm_service, st.session_state.db_manager, st.session_state.vector_store
    )
with tab4:
    render_matching_tab(
        llm_service,
        st.session_state.db_manager,
        st.session_state.vector_store,
        parse_md_to_result,
    )
with tab5:
    render_linkedin_tab(llm_service, li_username, li_password)
with tab6:
    render_database_tab(st.session_state.db_manager)
