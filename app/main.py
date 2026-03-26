import streamlit as st
import os
import json
import urllib.parse
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

# Load credentials from secrets.env if it exists
load_dotenv("secrets.env")

# Page Configuration
st.set_page_config(page_title="Funding Research App", layout="wide")

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
def get_llm_service():
    providers = ["openai", "groq", "gemini", "ollama"]
    env_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    default_index = providers.index(env_provider) if env_provider in providers else 0

    provider = st.sidebar.selectbox(
        "LLM Provider",
        providers,
        index=default_index,
        help="Select the LLM provider you want to use for analysis and matching."
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
        f"{provider.capitalize()} API Key",
        value=default_api_key,
        type="password",
        help=f"Enter your {provider.capitalize()} API key."
    )
    model = st.sidebar.text_input(
        "Model (Optional)",
        value=os.getenv("LLM_MODEL", ""),
        placeholder="e.g. gpt-4o, llama3-70b-8192",
        help="Specify a custom model name if supported by the provider."
    )

    if api_key or provider == "ollama":
        return LLMService(provider=provider, api_key=api_key, llm_model=model if model else None)
    return None

llm_service = get_llm_service()

# Sidebar - Settings
st.sidebar.title("Settings")
fit_username = st.sidebar.text_input(
    "FIT Username",
    value=os.getenv("FIT_USERNAME", ""),
    placeholder="your.email@uni-kassel.de",
    help="Your FIT Uni Kassel username (usually email)."
)
fit_password = st.sidebar.text_input(
    "FIT Password",
    value=os.getenv("FIT_PASSWORD", ""),
    type="password",
    help="Your FIT Uni Kassel password."
)
li_username = st.sidebar.text_input(
    "LinkedIn Username",
    value=os.getenv("LINKEDIN_USERNAME", ""),
    placeholder="your.email@example.com",
    help="Your LinkedIn login email."
)
li_password = st.sidebar.text_input(
    "LinkedIn Password",
    value=os.getenv("LINKEDIN_PASSWORD", ""),
    type="password",
    help="Your LinkedIn password."
)

# Main Header
st.title("Funding Research and Collaboration App")

if not llm_service:
    st.warning("Please configure your LLM Provider and API Key in the sidebar.")
    st.stop()

# Tab Layout
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Call Summarization",
    "FIT Search",
    "Company Indexing",
    "Matching & Hybrid Search",
    "LinkedIn Integration",
    "Database View"
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
def parse_md_to_result(content):
    """Parses metadata from .md summaries for matching service compatibility."""
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
    st.header("Research Call Analysis")
    call_url = st.text_input(
        "Enter Research Call URL",
        key="call_url_input",
        placeholder="https://example.com/research-funding-call",
        help="Paste the URL of a research funding call to analyze its content."
    )

    if st.button("Analyze Call"):
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

    summaries_dir = "data/summaries"
    os.makedirs(summaries_dir, exist_ok=True)
    saved_files = [f for f in os.listdir(summaries_dir) if f.endswith(".md")]

    col_load1, col_load2 = st.columns([3, 1])
    with col_load1:
        selected_file = st.selectbox("Gespeicherte Zusammenfassungen", saved_files, label_visibility="collapsed")
    with col_load2:
        if st.button("Laden"):
            with open(os.path.join(summaries_dir, selected_file), "r", encoding="utf-8") as f:
                loaded_content = f.read()
                st.session_state.last_call = parse_md_to_result(loaded_content)
                st.success(f"Geladen: {selected_file}")

    if "last_call" in st.session_state:
        result = st.session_state.last_call
        st.subheader(f"Analysis: {result.get('Thema', 'N/A')}")

        # Display as Markdown
        st.markdown(result.get("Beschreibung", "No description available."))

        st.write("### Metadata")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Thema:** {result.get('Thema')}")
            st.write(f"**Zielsetzung:** {result.get('Zielsetzung')}")
            st.write(f"**Deadline:** {result.get('Deadline')}")
            st.write(f"**Link:** {result.get('Link')}")
        with col2:
            st.write(f"**Budget:** {result.get('Budget')}")
            st.write(f"**Laufzeit:** {result.get('Laufzeit')}")
            st.write(f"**Prozess:** {result.get('Einstufig_Zweistufig')}")
            st.write(f"**Partner:** {result.get('Anzahl_Projektpartner')}")

        st.write(f"**Antragsberechtigt:** {result.get('Antragsberechtigt', 'N/A')}")

        if result.get("Andere_Metadaten"):
            st.write(f"**Andere Metadaten:** {result.get('Andere_Metadaten')}")

        # Tools: Copy and Email
        st.divider()
        st.write("### Tools")

        # Build the summary text for copy/email
        summary_text = f"""Zusammenfassung der Ausschreibung: {result.get('Thema')}
Link: {result.get('Link')}

{result.get('Beschreibung')}

### Metadaten
- Thema: {result.get('Thema')}
- Zielsetzung: {result.get('Zielsetzung')}
- Deadline: {result.get('Deadline')}
- Budget: {result.get('Budget')}
- Laufzeit: {result.get('Laufzeit')}
- Prozess: {result.get('Einstufig_Zweistufig')}
- Partner: {result.get('Anzahl_Projektpartner')}
- Antragsberechtigt: {result.get('Antragsberechtigt')}
"""
        st.subheader("Speichern & Kopieren")

        if st.button("Speichern", help="Speichert diese Zusammenfassung als .md Datei"):
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
    st.header("FIT Uni Kassel Search")
    fit_query = st.text_input(
        "Search for calls on FIT",
        placeholder="Künstliche Intelligenz",
        help="Enter search terms to find research calls in the FIT database."
    )
    if st.button("Search FIT"):
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
            st.warning("Please provide FIT credentials in the sidebar.")

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
    st.header("Company Website Indexing")
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

    if st.button("Index Companies"):
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
    st.write("### Recursive Folder Indexing")
    folder_path = st.text_input(
        "Enter Folder Path containing .url files",
        placeholder="/path/to/your/links/folder",
        help="Provide a local folder path to recursively search for and index .url files."
    )
    if st.button("Index from Folder"):
        if folder_path and os.path.exists(folder_path):
            indexer = IndexingService(llm_service, st.session_state.db_manager, st.session_state.vector_store)
            with st.status(f"Scanning {folder_path}...") as status:
                indexed = indexer.index_from_folder(folder_path, status_callback=lambda msg: status.update(label=msg))
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
    st.header("Match Companies to Calls")

    # Matching Section
    summaries_dir = "data/summaries"
    os.makedirs(summaries_dir, exist_ok=True)
    saved_calls = [f for f in os.listdir(summaries_dir) if f.endswith(".md")]

    selected_call_file = st.selectbox("Wähle einen gespeicherten Call", saved_calls)

    # Persistent storage for matches and topics
    matches_dir = "data/matches"
    topics_dir = "data/topics"
    os.makedirs(matches_dir, exist_ok=True)
    os.makedirs(topics_dir, exist_ok=True)

    if selected_call_file:
        call_name = selected_call_file.replace(".md", "")
        matches_path = os.path.join(matches_dir, f"{call_name}.json")
        topics_path = os.path.join(topics_dir, f"{call_name}.json")

        with open(os.path.join(summaries_dir, selected_call_file), "r", encoding="utf-8") as f:
            current_call_data = parse_md_to_result(f.read())

        st.subheader(f"Matching für: {current_call_data.get('Thema')}")

        matcher = MatchingService(llm_service, st.session_state.db_manager, st.session_state.vector_store)

        # Load existing matches if they exist
        if f"matches_{call_name}" not in st.session_state:
            if os.path.exists(matches_path):
                with open(matches_path, "r", encoding="utf-8") as f:
                    st.session_state[f"matches_{call_name}"] = json.load(f)
            else:
                st.session_state[f"matches_{call_name}"] = None

        if f"topics_{call_name}" not in st.session_state:
            if os.path.exists(topics_path):
                with open(topics_path, "r", encoding="utf-8") as f:
                    st.session_state[f"topics_{call_name}"] = json.load(f)
            else:
                st.session_state[f"topics_{call_name}"] = None

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            country_filter = st.text_input("Land filtern (z.B. Deutschland)", value="Deutschland")
            org_type_filter = st.selectbox("Organisationsart filtern", ["Alle", "Unternehmen", "Forschungseinrichtung", "Hochschule", "KMU"])

        if st.button("Find Matching Companies"):
            with st.spinner("Finding matches..."):
                query = f"Organization working on {current_call_data.get('Thema')} and {current_call_data.get('Zielsetzung')}"
                filters = {}
                if country_filter:
                    filters["country"] = country_filter
                if org_type_filter != "Alle":
                    filters["org_type"] = org_type_filter

                matches = matcher.hybrid_search(query, filters=filters, limit=10)
                if matches:
                    # Generate justifications
                    matches = matcher.generate_match_justification(current_call_data, matches)
                    st.session_state[f"matches_{call_name}"] = matches
                    with open(matches_path, "w", encoding="utf-8") as f:
                        json.dump(matches, f, ensure_ascii=False, indent=4)
                else:
                    st.session_state[f"matches_{call_name}"] = []
                    st.warning("Keine passenden Organisationen in der Datenbank gefunden.")

        if st.button("Suggest Research Topics"):
            # Use already found matches for context if available
            matched_companies = st.session_state.get(f"matches_{call_name}") or []

            with st.spinner("Generating research topic suggestions..."):
                topics = matcher.suggest_research_topics(
                    current_call_data,
                    user_context=st.session_state.get("user_context", ""),
                    matched_companies=matched_companies
                )
                st.session_state[f"topics_{call_name}"] = topics
                with open(topics_path, "w", encoding="utf-8") as f:
                    json.dump(topics, f, ensure_ascii=False, indent=4)

        # Display results
        if st.session_state.get(f"matches_{call_name}"):
            st.write("### Matching Organisations in Database:")
            for m in st.session_state[f"matches_{call_name}"]:
                with st.expander(f"**{m['name']}** - {m.get('industry', 'N/A')} ({m.get('country', 'N/A')})"):
                    st.write(f"**Begründung:** {m.get('justification', 'Keine Begründung vorhanden.')}")
                    st.write(f"**Zusammenfassung:** {m['summary']}")
                    st.write(f"**Typ:** {m.get('org_type', 'N/A')}")

        if st.session_state.get(f"topics_{call_name}"):
            st.write("### Suggested Topics:")
            for t in st.session_state[f"topics_{call_name}"]:
                st.markdown(t)

        st.divider()

    # Manual Search Section
    st.subheader("Manual Hybrid Search")
    search_query = st.text_input(
        "Enter search query (e.g. 'AI and Robotics')",
        placeholder="Machine Learning in Health",
        help="Search for companies in your database using semantic and keyword matching."
    )
    state_filter = st.text_input(
        "State Filter (Optional)",
        placeholder="Hessen",
        help="Filter results by German federal state (e.g., Hessen, Bayern)."
    )
    if st.button("Search Database"):
        matcher = MatchingService(llm_service, st.session_state.db_manager, st.session_state.vector_store)
        filters = {"state": state_filter} if state_filter else None
        results = matcher.hybrid_search(search_query, filters=filters)
        for r in results:
            st.info(f"**{r['name']}** ({r['state']})")
            st.write(r['summary'])

    # Internet Discovery Section
    st.subheader("Discover New Companies on the Internet")
    internet_topic = st.text_input(
        "Topic for internet search",
        placeholder="Innovative startups in robotics Germany",
        help="Search the web for new companies matching this topic."
    )
    if st.button("Search Internet"):
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
    st.header("LinkedIn Contacts for Call Matching")
    if li_username and li_password:
        li_service = LinkedInService(llm_service, li_username, li_password)
        if st.button("Fetch and Match Contacts"):
            if "last_call" in st.session_state:
                with st.spinner("Fetching contacts and matching..."):
                    contacts = li_service.get_first_degree_contacts()
                    if contacts:
                        matches = li_service.find_matching_contacts_for_call(contacts, st.session_state.last_call)
                        st.write(f"Matched {len(matches)} contacts:")
                        for contact in matches:
                            c_name = f"{contact.get('firstName')} {contact.get('lastName')}"
                            st.write(f"**{c_name}** - {contact.get('occupation')}")
                            if st.button(f"Generate Message for {contact.get('firstName')}", key=contact.get('public_id')):
                                msg = li_service.generate_outreach_message(c_name, "his/her company", st.session_state.last_call)
                                st.text_area("Message:", value=msg, height=200)
                    else:
                        st.info("No LinkedIn contacts found. Check your credentials.")
            else:
                st.warning("Please analyze a research call in the first tab first.")
    else:
        st.warning("Please provide LinkedIn credentials in the sidebar.")

# Feature 6: Database View
with tab6:
    st.header("Indexed Companies Database")
    if st.button("Refresh Database View"):
        st.rerun()

    companies = st.session_state.db_manager.get_all_companies()
    if companies:
        st.write(f"Total indexed companies: {len(companies)}")

        # Convert to list of dicts for dataframe
        data = []
        for c in companies:
            data.append({
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

        edited_data = st.data_editor(
            data,
            width="stretch",
            num_rows="dynamic",
            key="db_editor"
        )

        if st.button("Speichern"):
            # Prepare data for update
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
                st.success("Änderungen gespeichert!")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Speichern: {e}")

        # Detailed view in expanders
        st.subheader("Detailed Organization Profiles")
        for c in companies:
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
