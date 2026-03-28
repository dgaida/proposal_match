import streamlit as st
import os
import json
import urllib.parse
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from app.services.llm_service import LLMService
from app.services.scraper_service import ScraperService
from app.services.analyzer_service import AnalyzerService
from app.services.fit_service import FITService
from app.services.indexing_service import IndexingService
from app.services.matching_service import MatchingService
from app.services.linkedin_service import LinkedInService
from app.utils.db_manager import DBManager
from app.utils.vector_store import VectorStore
from app.utils.translations import translate
from app.utils.file_utils import get_file_age_days

# Load credentials from secrets.env if it exists
load_dotenv("secrets.env")

# Language Selection in Session State
if "lang" not in st.session_state:
    st.session_state.lang = "de"

# Page Configuration
st.set_page_config(page_title=translate("page_title", st.session_state.lang), layout="wide")

# Persistent Storage Initialization
if "db_manager" not in st.session_state:
    st.session_state.db_manager = DBManager()
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
    """Initializes the LLM service based on sidebar configuration.

    Returns:
        Optional[LLMService]: The initialized LLMService or None if config is missing.
    """
    providers = ["openai", "groq", "gemini", "ollama"]
    env_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    default_index = providers.index(env_provider) if env_provider in providers else 0

    provider = st.sidebar.selectbox(
        translate("llm_provider", st.session_state.lang),
        providers,
        index=default_index,
        help=translate("llm_help", st.session_state.lang)
    )

    # Get default API key based on provider
    default_api_key = ""
    if provider == "openai":
        default_api_key = os.getenv("OPENAI_API_KEY", "")
    elif provider == "groq":
        default_api_key = os.getenv("GROQ_API_KEY", "")
    elif provider == "gemini":
        default_api_key = os.getenv("GEMINI_API_KEY", "")

    api_key = st.sidebar.text_input(
        f"{provider.capitalize()} {translate('api_key', st.session_state.lang)}",
        value=default_api_key,
        type="password",
        help=translate("api_key_help", st.session_state.lang, provider=provider.capitalize())
    )
    model = st.sidebar.text_input(
        translate("model_optional", st.session_state.lang),
        value=os.getenv("LLM_MODEL", ""),
        placeholder="e.g. gpt-4o, llama3-70b-8192",
        help=translate("model_help", st.session_state.lang)
    )

    if api_key or provider == "ollama":
        return LLMService(provider=provider, api_key=api_key, llm_model=model if model else None)
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
        label_visibility="collapsed"
    )
    if lang_options[selected_lang_name] != st.session_state.lang:
        st.session_state.lang = lang_options[selected_lang_name]
        st.rerun()

# Sidebar - Settings
st.sidebar.title(translate("settings", st.session_state.lang))
fit_username = st.sidebar.text_input(
    translate("fit_username", st.session_state.lang),
    value=os.getenv("FIT_USERNAME", ""),
    placeholder="your.email@uni-kassel.de",
    help="Your FIT Uni Kassel username (usually email)."
)
fit_password = st.sidebar.text_input(
    translate("fit_password", st.session_state.lang),
    value=os.getenv("FIT_PASSWORD", ""),
    type="password",
    help="Your FIT Uni Kassel password."
)
li_username = st.sidebar.text_input(
    translate("linkedin_username", st.session_state.lang),
    value=os.getenv("LINKEDIN_USERNAME", ""),
    placeholder="your.email@example.com",
    help="Your LinkedIn login email."
)
li_password = st.sidebar.text_input(
    translate("linkedin_password", st.session_state.lang),
    value=os.getenv("LINKEDIN_PASSWORD", ""),
    type="password",
    help="Your LinkedIn password."
)

# Main Header
st.title(translate("app_title", st.session_state.lang))

if not llm_service:
    st.warning(translate("configure_llm_warning", st.session_state.lang))
    st.stop()

# Tab Layout
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    translate("tab_summarization", st.session_state.lang),
    translate("tab_fit", st.session_state.lang),
    translate("tab_indexing", st.session_state.lang),
    translate("tab_matching", st.session_state.lang),
    translate("tab_linkedin", st.session_state.lang),
    translate("tab_database", st.session_state.lang)
])

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

# Utility functions
def parse_md_to_result(content: str) -> Dict[str, Any]:
    """Parses metadata from .md summaries for matching service compatibility.

    Args:
        content (str): The Markdown content of the summary.

    Returns:
        Dict[str, Any]: A dictionary containing extracted metadata.
    """
    result = {}
    lines = content.split('\n')
    for line in lines:
        if line.startswith("Zusammenfassung der Ausschreibung: "):
            result['Thema'] = line.replace("Zusammenfassung der Ausschreibung: ", "").strip()
        elif line.startswith("Link: "):
            result['Link'] = line.replace("Link: ", "").strip()
        elif line.startswith("- Thema: "):
            result['Thema'] = line.replace("- Thema: ", "").strip()
        elif line.startswith("- Zielsetzung: "):
            result['Zielsetzung'] = line.replace("- Zielsetzung: ", "").strip()
        elif line.startswith("- Deadline: "):
            result['Deadline'] = line.replace("- Deadline: ", "").strip()
        elif line.startswith("- Budget: "):
            result['Budget'] = line.replace("- Budget: ", "").strip()
        elif line.startswith("- Laufzeit: "):
            result['Laufzeit'] = line.replace("- Laufzeit: ", "").strip()
        elif line.startswith("- Prozess: "):
            result['Einstufig_Zweistufig'] = line.replace("- Prozess: ", "").strip()
        elif line.startswith("- Partner: "):
            result['Anzahl_Projektpartner'] = line.replace("- Partner: ", "").strip()
        elif line.startswith("- Antragsberechtigt: "):
            result['Antragsberechtigt'] = line.replace("- Antragsberechtigt: ", "").strip()
        elif line.startswith("- Antragsberechtigt_Details: "):
            result['Antragsberechtigt_Details'] = line.replace("- Antragsberechtigt_Details: ", "").strip()
        elif line.startswith("- Sitz der Organisation: "):
            result['Sitz_der_Organisation'] = line.replace("- Sitz der Organisation: ", "").strip()

    try:
        desc_start = content.find("Link:")
        desc_start = content.find("\n", desc_start) + 1
        desc_end = content.find("### Metadaten")
        result['Beschreibung'] = content[desc_start:desc_end].strip()
    except Exception:
        result['Beschreibung'] = "No description found."

    return result

# Feature 1: Call Summarization
with tab1:
    st.header(translate("research_call_analysis", st.session_state.lang))

    # Auto-load logic for the very first startup
    summaries_dir = "data/summaries"
    os.makedirs(summaries_dir, exist_ok=True)
    saved_files = sorted([f for f in os.listdir(summaries_dir) if f.endswith(".md")])

    if "last_call" not in st.session_state and saved_files:
        first_file = saved_files[0]
        try:
            with open(os.path.join(summaries_dir, first_file), "r", encoding="utf-8") as f:
                st.session_state.last_call = parse_md_to_result(f.read())
                st.session_state.current_selected_file = first_file
        except Exception:
            pass

    def load_selected_summary():
        if "summary_selector" in st.session_state:
            filename = st.session_state.summary_selector
            filepath = os.path.join(summaries_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    st.session_state.last_call = parse_md_to_result(f.read())
                    st.session_state.current_selected_file = filename

    call_url = st.text_input(
        translate("enter_call_url", st.session_state.lang),
        key="call_url_input",
        placeholder="https://example.com/research-funding-call",
        help="Paste the URL of a research funding call to analyze its content."
    )

    if st.button(translate("analyze_call_button", st.session_state.lang)):
        scraper = ScraperService()
        analyzer = AnalyzerService(llm_service)
        with st.status("Fetching and analyzing...") as status:
            text = scraper.fetch_page_content(call_url)
            if text:
                try:
                    result = analyzer.analyze_research_call(
                        text,
                        url=call_url,
                        status_callback=lambda msg: status.update(label=msg)
                    )
                    if result:
                        status.update(label="Analysis Complete!", state="complete")
                        st.session_state.last_call = result # Store for matching and persistence
                    else:
                        status.update(label="Failed to analyze the call.", state="error")
                        st.error("Failed to analyze the call: Structured data extraction returned no result.")
                except Exception as e:
                    status.update(label="Analysis Failed.", state="error")
                    st.error(f"Error analyzing research call: {str(e)}")
            else:
                status.update(label="Failed to fetch URL.", state="error")
                st.error("Failed to fetch the URL content.")

    col_load1, col_load2 = st.columns([3, 1])
    with col_load1:
        default_idx = 0
        if "current_selected_file" in st.session_state and st.session_state.current_selected_file in saved_files:
            default_idx = saved_files.index(st.session_state.current_selected_file)

        selected_file = st.selectbox(
            translate("saved_summaries", st.session_state.lang),
            saved_files,
            index=default_idx,
            label_visibility="collapsed",
            key="summary_selector",
            on_change=load_selected_summary
        )

    if "last_call" in st.session_state:
        result = st.session_state.last_call

        # Display currently selected call and its age
        current_file = st.session_state.get("current_selected_file", "")
        age_str = ""
        if current_file:
            age_days = get_file_age_days(os.path.join(summaries_dir, current_file))
            age_str = f" ({translate('age_days', st.session_state.lang, days=age_days)})"

        st.info(f"{translate('active_call', st.session_state.lang)} **{result.get('Thema', 'N/A')}**{age_str}")

        st.subheader(f"Analysis: {result.get('Thema', 'N/A')}")

        # Display as Markdown
        st.markdown(result.get("Beschreibung", "No description available."))

        st.write(f"### {translate('metadata', st.session_state.lang)}")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Thema:** {result.get('Thema')}")
            st.write(f"**Zielsetzung:** {result.get('Zielsetzung')}")
            st.write(f"**Deadline:** {result.get('Deadline')}")
            st.write(f"**Sitz der Organisation:** {result.get('Sitz_der_Organisation', 'N/A')}")
        with col2:
            st.write(f"**Budget:** {result.get('Budget')}")
            st.write(f"**Laufzeit:** {result.get('Laufzeit')}")
            st.write(f"**Prozess:** {result.get('Einstufig_Zweistufig')}")
            st.write(f"**Link:** {result.get('Link')}")

        st.write(f"**Partner:** {result.get('Anzahl_Projektpartner')}")
        st.write(f"**Antragsberechtigt:** {result.get('Antragsberechtigt', 'N/A')}")
        st.write(f"**Antragsberechtigt_Details:** {result.get('Antragsberechtigt_Details', 'N/A')}")

        if result.get("Andere_Metadaten"):
            st.write(f"**Andere Metadaten:** {result.get('Andere_Metadaten')}")

        # Tools: Copy and Email
        st.divider()
        st.write(f"### {translate('tools', st.session_state.lang)}")

        # Build the summary text for copy/email
        summary_text = f"""Zusammenfassung der Ausschreibung: {result.get('Thema')}
Link: {result.get('Link')}

{result.get('Beschreibung')}

### Metadaten
- Thema: {result.get('Thema')}
- Zielsetzung: {result.get('Zielsetzung')}
- Deadline: {result.get('Deadline')}
- Sitz der Organisation: {result.get('Sitz_der_Organisation')}
- Budget: {result.get('Budget')}
- Laufzeit: {result.get('Laufzeit')}
- Prozess: {result.get('Einstufig_Zweistufig')}
- Partner: {result.get('Anzahl_Projektpartner')}
- Antragsberechtigt: {result.get('Antragsberechtigt')}
- Antragsberechtigt_Details: {result.get('Antragsberechtigt_Details')}
"""
        st.subheader(translate("save_and_copy", st.session_state.lang))

        if st.button(translate("save_button", st.session_state.lang), help="Speichert diese Zusammenfassung als .md Datei"):
            filename = f"{result.get('Thema', 'summary')[:50]}.md".replace(" ", "_").replace("/", "_")
            filepath = os.path.join(summaries_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(summary_text)
            st.success(f"Gespeichert als {filename}")
            st.rerun()

        st.divider()
        st.code(summary_text, language="markdown")

        st.subheader("Versenden")

        # Email Template
        email_body = f"Hallo ...,\n\nich habe die Ausschreibung \"{result.get('Thema')}\" analysieren lassen. Hier ist die Zusammenfassung:\n\n{summary_text}"

        # Create mailto link
        subject = f"Zusammenfassung der Ausschreibung: {result.get('Thema')}"
        mailto_link = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(email_body)}"

        st.markdown(f'<a href="{mailto_link}" target="_blank" style="text-decoration: none;"><button style="background-color: #f63366; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer;">📧 Als Mail senden</button></a>', unsafe_allow_html=True)

# Feature 2: FIT Search
with tab2:
    st.header(translate("fit_search_title", st.session_state.lang))

    # Show cache age for FIT results
    fit_cache_path = "data/fit_cache.json"
    if os.path.exists(fit_cache_path):
        age_days = get_file_age_days(fit_cache_path)
        st.info(f"{translate('tab_fit', st.session_state.lang)}: {translate('age_days', st.session_state.lang, days=age_days)}")

    fit_query = st.text_input(
        translate("tab_fit", st.session_state.lang),
        placeholder="Künstliche Intelligenz",
        help="Enter search terms to find research calls in the FIT database."
    )
    if st.button(translate("search_fit_button", st.session_state.lang)):
        if fit_username and fit_password:
            fit_service = FITService(llm_service)
            with st.status("Initializing FIT Search...") as status:
                if fit_service.login(fit_username, fit_password, status_callback=lambda msg: status.update(label=msg)):
                    results = fit_service.search_calls(fit_query, status_callback=lambda msg: status.update(label=msg))
                    summary = fit_service.summarize_results(results, status_callback=lambda msg: status.update(label=msg))

                    st.session_state.fit_results = {
                        "results": results,
                        "summary": summary
                    }

                    # Auto-save to cache
                    os.makedirs("data", exist_ok=True)
                    with open("data/fit_cache.json", "w", encoding="utf-8") as f:
                        json.dump(st.session_state.fit_results, f, ensure_ascii=False, indent=4)

                    status.update(label="Search and Analysis Complete!", state="complete")
                else:
                    status.update(label="Login to FIT failed.", state="error")
                    st.error("Login to FIT failed.")
        else:
            st.warning(translate("provide_fit_creds", st.session_state.lang))

    if st.session_state.fit_results:
        results = st.session_state.fit_results.get("results", [])
        summary = st.session_state.fit_results.get("summary", "")

        st.write(f"Found {len(results)} results.")
        for r in results:
            with st.expander(r.get("title") or r.get("englishTitle")):
                st.write(r.get("description") or r.get("shortDescription"))

        st.subheader("Summary of Results")
        st.write(summary)

# Feature 3: Company Indexing
with tab3:
    st.header(translate("company_indexing_title", st.session_state.lang))
    st.write("Upload a file with company hyperlinks (one per line) or enter them manually.")
    company_links_input = st.text_area(
        "Enter Company Links (one per line)",
        placeholder="https://company-a.com\nhttps://company-b.de",
        help="Enter one or more company website URLs to index."
    )
    uploaded_file = st.file_uploader(
        "Or upload a text file with links",
        type=["txt"],
        help="Upload a plain text file containing one URL per line."
    )

    if st.button(translate("index_companies_button", st.session_state.lang)):
        links = []
        if company_links_input:
            links.extend([link_item.strip() for link_item in company_links_input.split("\n") if link_item.strip()])
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8")
            links.extend([link_item.strip() for link_item in content.split("\n") if link_item.strip()])

        if links:
            indexer = IndexingService(llm_service, st.session_state.db_manager, st.session_state.vector_store)
            progress_bar = st.progress(0)
            for i, link in enumerate(links):
                with st.status(f"Indexing {link}..."):
                    indexer.index_companies_from_links([link])
                progress_bar.progress((i + 1) / len(links))
            st.success("Indexing Complete!")
        else:
            st.warning("Please provide links to index.")

    st.divider()
    st.write(f"### {translate('recursive_folder_indexing', st.session_state.lang)}")
    folder_path = st.text_input(
        "Enter Folder Path containing .url files",
        placeholder="/path/to/your/links/folder",
        help="Provide a local folder path to recursively search for and index .url files."
    )
    folder_limit = st.number_input("Limit für Ordner-Indexierung", min_value=1, value=25, step=1, help="Maximale Anzahl neuer Unternehmen, die aus dem Ordner indexiert werden sollen.")
    if st.button(translate("index_from_folder_button", st.session_state.lang)):
        if folder_path and os.path.exists(folder_path):
            indexer = IndexingService(llm_service, st.session_state.db_manager, st.session_state.vector_store)
            with st.status(f"Scanning {folder_path}...") as status:
                indexed = indexer.index_from_folder(folder_path, limit=folder_limit, status_callback=lambda msg: status.update(label=msg))
                status.update(label=f"Indexed {len(indexed)} URLs from folder.", state="complete")
            st.success(f"Successfully indexed {len(indexed)} companies from folder.")
            if indexed:
                with st.expander("Show indexed companies/URLs"):
                    for url in indexed:
                        st.write(f"- {url}")
        else:
            st.error("Invalid or empty folder path.")

# Feature 4: Hybrid Search and Matching
with tab4:
    st.header(translate("matching_title", st.session_state.lang))

    # Unified state for results
    if "current_matches" not in st.session_state:
        st.session_state.current_matches = []
    if "current_topics" not in st.session_state:
        st.session_state.current_topics = []
    if "last_queries" not in st.session_state:
        st.session_state.last_queries = []

    search_mode = st.radio(
        translate("search_mode", st.session_state.lang),
        [translate("auto_matching", st.session_state.lang), translate("manual_matching", st.session_state.lang)],
        help="Wählen Sie 'Automatisch', um basierend auf einem Call zu suchen, oder 'Manuell', um einen eigenen Suchbegriff einzugeben."
    )

    matcher = MatchingService(llm_service, st.session_state.db_manager, st.session_state.vector_store)
    current_call_data = None
    call_name = "manual_search"

    if search_mode == translate("auto_matching", st.session_state.lang):
        summaries_dir = "data/summaries"
        os.makedirs(summaries_dir, exist_ok=True)
        saved_calls = [f for f in os.listdir(summaries_dir) if f.endswith(".md")]
        selected_call_file = st.selectbox(translate("saved_summaries", st.session_state.lang), saved_calls)

        if selected_call_file:
            call_name = selected_call_file.replace(".md", "")
            with open(os.path.join(summaries_dir, selected_call_file), "r", encoding="utf-8") as f:
                current_call_data = parse_md_to_result(f.read())
            st.info(f"{translate('active_call', st.session_state.lang)} **{current_call_data.get('Thema')}**")
    else:
        manual_query = st.text_input(
            "Suchbegriff eingeben",
            placeholder="z.B. KI im Maschinenbau",
            help="Geben Sie technische Anforderungen oder Fachbereiche ein."
        )

    st.subheader(translate("filters", st.session_state.lang))
    companies = st.session_state.db_manager.get_all_companies()
    countries = sorted(list({c.country for c in companies if c.country}))
    states = sorted(list({c.state for c in companies if c.state}))

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        # Pre-select Deutschland if it's a German call
        default_country_index = 0
        if current_call_data and current_call_data.get("Sitz_der_Organisation") == "Deutschland":
            if "Deutschland" in countries:
                default_country_index = countries.index("Deutschland") + 1

        country_filter = st.selectbox("Land filtern", ["Alle"] + countries, index=default_country_index, key="hybrid_country_filter")
    with col_f2:
        state_filter = st.selectbox("Bundesland filtern", ["Alle"] + states, index=0, key="hybrid_state_filter")
    with col_f3:
        org_type_filter = st.selectbox("Organisationsart filtern", ["Alle", "Unternehmen", "Forschungseinrichtung", "Hochschule", "KMU"], key="hybrid_org_filter")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(translate("find_organisations_button", st.session_state.lang)):
            with st.spinner("Suche läuft..."):
                queries = []
                if search_mode == translate("auto_matching", st.session_state.lang) and current_call_data:
                    # Query generation and caching
                    queries_dir = "data/queries"
                    os.makedirs(queries_dir, exist_ok=True)
                    query_cache_path = os.path.join(queries_dir, f"{call_name}_multiple.json")

                    if os.path.exists(query_cache_path):
                        age_days = get_file_age_days(query_cache_path)
                        st.info(f"{translate('tab_matching', st.session_state.lang)} Cache: {translate('age_days', st.session_state.lang, days=age_days)}")
                        with open(query_cache_path, "r", encoding="utf-8") as f:
                            queries = json.load(f)
                    else:
                        queries = matcher.generate_multiple_matching_queries(current_call_data, n=5)
                        with open(query_cache_path, "w", encoding="utf-8") as f:
                            json.dump(queries, f, ensure_ascii=False)
                elif search_mode == "Manuelle Hybrid-Suche" and manual_query:
                    # Optimize manual query first
                    optimized_query = matcher.rephrase_query(manual_query)
                    queries = matcher.generate_multiple_matching_queries(optimized_query, n=5)
                    if not current_call_data:
                        current_call_data = {"Thema": manual_query, "Beschreibung": f"Manuelle Suche nach: {manual_query}"}

                if queries:
                    st.session_state.last_queries = queries
                    filters = {}
                    if country_filter != "Alle":
                        filters["country"] = country_filter
                    if state_filter != "Alle":
                        filters["state"] = state_filter
                    if org_type_filter != "Alle":
                        if org_type_filter == "KMU":
                            filters["org_type"] = "Unternehmen"
                            filters["kmu_status"] = True
                        else:
                            filters["org_type"] = org_type_filter

                    # Aggregate results from all queries
                    all_matches_dict = {}
                    for q in queries:
                        query_matches = matcher.hybrid_search(q, filters=filters, limit=10)
                        for m in query_matches:
                            url = m['url']
                            if url not in all_matches_dict or m['relevance'] > all_matches_dict[url]['relevance']:
                                all_matches_dict[url] = m

                    # Sort by relevance
                    matches = sorted(all_matches_dict.values(), key=lambda x: x['relevance'], reverse=True)

                    if matches:
                        if current_call_data:
                            # Use top matches for justification to save tokens if there are many
                            matches = matcher.generate_match_justification(current_call_data, matches[:10])
                        st.session_state.current_matches = matches
                    else:
                        st.session_state.current_matches = []
                        st.warning("Keine passenden Organisationen in der Datenbank gefunden.")
                else:
                    st.warning("Bitte geben Sie einen Suchbegriff ein oder wählen Sie einen Call aus.")

    with col_btn2:
        if st.button(translate("suggest_topics_button", st.session_state.lang)):
            if not current_call_data and search_mode == "Manuelle Hybrid-Suche":
                # Create a minimal call data from manual query if no call selected
                current_call_data = {"Thema": manual_query, "Beschreibung": f"Manuelle Suche nach: {manual_query}"}

            if current_call_data:
                with st.spinner("Generiere Vorschläge..."):
                    topics = matcher.suggest_research_topics(
                        current_call_data,
                        user_context=st.session_state.get("user_context", ""),
                        matched_companies=st.session_state.current_matches
                    )
                    st.session_state.current_topics = topics
            else:
                st.warning("Bitte wählen Sie einen Call aus oder geben Sie einen Suchbegriff für den Kontext an.")

    # Unified Display
    if st.session_state.last_queries:
        st.write("### Verwendete Suchanfragen:")
        for q in st.session_state.last_queries:
            st.info(q)

    if st.session_state.current_matches:
        st.write(f"### {translate('matching_title', st.session_state.lang)}:")
        for m in st.session_state.current_matches:
            relevance_pct = f"{int(m.get('relevance', 0) * 100)}%"
            with st.expander(f"**{m['name']}** - Relevance: {relevance_pct} - {m.get('industry', 'N/A')} ({m.get('country', 'N/A')})"):
                if m.get('justification'):
                    st.write(f"**{translate('justification', st.session_state.lang)}:** {m['justification']}")
                st.write(f"**{translate('summary', st.session_state.lang)}:** {m['summary']}")

                st.divider()
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    url = m.get('url', 'N/A')
                    if url != 'N/A':
                        st.write(f"**{translate('website', st.session_state.lang)}:** [{url}]({url})")
                    else:
                        st.write(f"**{translate('website', st.session_state.lang)}:** N/A")
                    st.write(f"**{translate('type', st.session_state.lang)}:** {m.get('org_type', 'N/A')}")
                    st.write(f"**{translate('city', st.session_state.lang)}:** {m.get('city', 'N/A')}")
                with col_info2:
                    st.write(f"**{translate('employees', st.session_state.lang)}:** {m.get('employees_count', 'N/A')}")
                    st.write(f"**{translate('sme_status', st.session_state.lang)}:** {'Ja' if m.get('kmu_status') else 'Nein'}")

    if st.session_state.current_topics:
        st.write("### Vorschläge für Forschungsthemen:")
        for t in st.session_state.current_topics:
            st.markdown(t)

    st.divider()

    # Internet Discovery Section
    st.subheader(translate("discover_internet", st.session_state.lang))
    internet_topic = st.text_input(
        "Topic for internet search",
        placeholder="Innovative startups in robotics Germany",
        help="Search the web for new companies matching this topic."
    )
    if st.button(translate("search_internet_button", st.session_state.lang)):
        matcher = MatchingService(llm_service, st.session_state.db_manager, st.session_state.vector_store)
        with st.spinner("Searching the web..."):
            web_results = matcher.search_internet_for_companies(internet_topic)
            for res in web_results:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**[{res['name']}]({res['url']})**")
                    st.write(res['snippet'])
                with col2:
                    if st.button("Index this company", key=res['url']):
                        indexer = IndexingService(llm_service, st.session_state.db_manager, st.session_state.vector_store)
                        indexer.index_companies_from_links([res['url']])
                        st.success("Indexed!")

# Feature 5: LinkedIn Integration
with tab5:
    st.header(translate("linkedin_matching_title", st.session_state.lang))
    st.warning(translate("linkedin_notice", st.session_state.lang))
    if li_username and li_password:
        li_service = LinkedInService(llm_service, li_username, li_password)
        li_limit = st.number_input("Anzahl zu suchender Kontakte", min_value=1, value=20, step=1, help="Begrenzt die Anzahl der abgerufenen 1st-degree Kontakte.")
        if st.button(translate("fetch_contacts_button", st.session_state.lang)):
            if "last_call" in st.session_state:
                with st.status("LinkedIn processing...") as status:
                    contacts = li_service.get_first_degree_contacts(limit=li_limit, status_callback=lambda msg: status.update(label=msg))
                    if contacts:
                        result = li_service.find_matching_contacts_for_call(
                            contacts,
                            st.session_state.last_call,
                            status_callback=lambda msg: status.update(label=msg)
                        )
                        matches = result.get("matches", [])
                        identified_names = result.get("identified_names", [])
                        criteria = result.get("criteria", "")

                        if identified_names:
                            status.update(label=f"LLM identified {len(identified_names)} potential matches!", state="complete")

                            st.subheader("Matching Criteria")
                            st.write(criteria)

                            st.subheader("Contacts identified by LLM")
                            st.write(", ".join(identified_names))

                            if matches:
                                st.subheader("Final Matching Contacts")
                                for contact in matches:
                                    c_name = f"{contact.get('firstName')} {contact.get('lastName')}"
                                    st.write(f"**{c_name}** - {contact.get('occupation')}")
                                    if st.button(f"Generate Message for {contact.get('firstName')}", key=contact.get('public_id')):
                                        msg = li_service.generate_outreach_message(c_name, "his/her company", st.session_state.last_call)
                                        st.text_area("Message:", value=msg, height=200)
                            else:
                                st.info("No matching contacts found in the detailed profiles.")
                        else:
                            status.update(label="No matches found.", state="error")
                            st.info("No matching LinkedIn contacts identified by the LLM.")
                    else:
                        status.update(label="No contacts found.", state="error")
                        st.info("No LinkedIn contacts found. Check your credentials.")
            else:
                st.warning(translate("analyze_first_warn", st.session_state.lang))
    else:
        st.warning(translate("provide_li_creds", st.session_state.lang))

# Feature 6: Database View
with tab6:
    st.header(translate("database_title", st.session_state.lang))
    if st.button(translate("refresh_db_button", st.session_state.lang)):
        removed = st.session_state.db_manager.deduplicate_companies()
        if removed > 0:
            st.success(f"{removed} Duplikate wurden entfernt.")
        else:
            st.info("Keine Duplikate gefunden.")
        st.rerun()

    companies = st.session_state.db_manager.get_all_companies()
    if companies:
        # Filtering logic
        st.subheader("Filter & Suche")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            name_filter = st.text_input("Name suchen", placeholder="Unternehmen A", key="db_name_filter")
        with col_f2:
            countries = sorted(list({c.country for c in companies if c.country}))
            country_filter = st.selectbox("Land filtern", ["Alle"] + countries, key="db_country_filter")
        with col_f3:
            states = sorted(list({c.state for c in companies if c.state}))
            state_filter = st.selectbox("Bundesland filtern", ["Alle"] + states, key="db_state_filter")
        with col_f4:
            org_types = sorted(list({c.org_type for c in companies if c.org_type}))
            org_filter_options = ["Alle"] + org_types
            if "KMU" not in org_filter_options:
                org_filter_options.append("KMU")
            org_type_filter = st.selectbox("Organisationsart filtern", org_filter_options, key="db_org_type_filter")

        # Convert to list of dicts for dataframe
        data = []
        for c in companies:
            # Apply filters
            if name_filter and name_filter.lower() not in (c.name or "").lower():
                continue
            if country_filter != "Alle" and c.country != country_filter:
                continue
            if state_filter != "Alle" and c.state != state_filter:
                continue
            if org_type_filter != "Alle":
                if org_type_filter == "KMU":
                    if c.org_type != "Unternehmen" or not c.kmu_status:
                        continue
                elif c.org_type != org_type_filter:
                    continue

            data.append({
                "Select": False,
                "Name": c.name,
                "URL": c.url,
                "Industry": c.industry,
                "Land": c.country,
                "Organisationsart": c.org_type,
                "State": c.state,
                "City": c.city,
                "Employees": c.employees_count,
                "SME": c.kmu_status,
                "Research Active": c.research_active,
                "Summary": c.summary,
                "Products": c.products
            })

        # Sort by Name (case-insensitive)
        data.sort(key=lambda x: (x.get("Name") or "").lower())

        st.write(f"Anzahl angezeigter Einträge: {len(data)}")

        edited_data = st.data_editor(
            data,
            width="stretch",
            num_rows="dynamic",
            key="db_editor"
        )

        # Check for changes in data_editor and auto-save
        db_edits = st.session_state.get("db_editor", {})
        if db_edits.get("edited_rows") or db_edits.get("added_rows") or db_edits.get("deleted_rows"):
            # Prepare data for update from the current state of edited_data
            update_list = []
            for row in edited_data:
                update_list.append({
                    "name": row.get("Name"),
                    "url": row.get("URL"),
                    "industry": row.get("Industry"),
                    "country": row.get("Land"),
                    "org_type": row.get("Organisationsart"),
                    "state": row.get("State"),
                    "city": row.get("City"),
                    "employees_count": row.get("Employees"),
                    "kmu_status": row.get("SME"),
                    "research_active": row.get("Research Active"),
                    "summary": row.get("Summary"),
                    "products": row.get("Products")
                })

            try:
                st.session_state.db_manager.update_companies(update_list)
                st.toast("Änderungen automatisch gespeichert!")
            except Exception as e:
                st.error(f"Fehler beim automatischen Speichern: {e}")

        # Detailed view in expanders
        st.subheader("Detailed Organization Profiles")

        # Determine selected URLs safely
        selected_urls = []
        if edited_data is not None:
            if isinstance(edited_data, list):
                selected_urls = [row.get("URL") for row in edited_data if isinstance(row, dict) and row.get("Select") and row.get("URL")]
            else: # Handle case if it's a DataFrame
                try:
                    selected_urls = edited_data[edited_data["Select"]]["URL"].tolist()
                except Exception:
                    selected_urls = []

        for c in companies:
            if c.url in selected_urls:
                with st.expander(f"{c.name or c.url}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**URL:** {c.url}")
                        st.write(f"**Industry:** {c.industry}")
                        st.write(f"**Country:** {c.country}")
                        st.write(f"**Organization Type:** {c.org_type}")
                        st.write(f"**State:** {c.state}")
                        st.write(f"**City:** {c.city}")
                    with col2:
                        st.write(f"**Employees:** {c.employees_count}")
                        st.write(f"**SME:** {c.kmu_status}")
                        st.write(f"**Research Active:** {c.research_active}")

                    st.write("**Summary:**")
                    st.write(c.summary)
                    st.write("**Products/Services:**")
                    st.write(c.products)
    else:
        st.info("No companies indexed yet. Go to 'Company Indexing' to add some.")
