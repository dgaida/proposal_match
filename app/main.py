import streamlit as st
import os
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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Call Summarization",
    "FIT Search",
    "Company Indexing",
    "Matching & Hybrid Search",
    "LinkedIn Integration"
])

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
        with st.spinner("Fetching and analyzing..."):
            text = scraper.fetch_page_content(call_url)
            if text:
                result = analyzer.analyze_research_call(text, url=call_url)
                if result:
                    st.success("Analysis Complete!")
                    st.session_state.last_call = result # Store for matching and persistence
                else:
                    st.error("Failed to analyze the call.")
            else:
                st.error("Failed to fetch the URL content.")

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
"""
        st.subheader("Kopieren")
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
            with st.spinner("Logging in and searching..."):
                if fit_service.login(fit_username, fit_password):
                    results = fit_service.search_calls(fit_query)
                    st.write(f"Found {len(results)} results.")
                    for r in results:
                        with st.expander(r.get("title") or r.get("englishTitle")):
                            st.write(r.get("description") or r.get("shortDescription"))

                    st.subheader("Summary of Results")
                    summary = fit_service.summarize_results(results)
                    st.write(summary)
                else:
                    st.error("Login to FIT failed.")
        else:
            st.warning("Please provide FIT credentials in the sidebar.")

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
                indexed = indexer.index_from_folder(folder_path)
                status.update(label=f"Indexed {len(indexed)} URLs from folder.", state="complete")
            st.success(f"Successfully indexed {len(indexed)} companies from folder.")
        else:
            st.error("Invalid or empty folder path.")

# Feature 4: Hybrid Search and Matching
with tab4:
    st.header("Match Companies to Calls")

    # Matching Section
    if "last_call" in st.session_state:
        st.subheader("Matching for analyzed call:")
        st.write(st.session_state.last_call.get("Thema"))

        matcher = MatchingService(llm_service, st.session_state.db_manager, st.session_state.vector_store)
        if st.button("Find Matching Companies"):
            with st.spinner("Finding matches..."):
                query = f"Company working on {st.session_state.last_call.get('Thema')} and {st.session_state.last_call.get('Zielsetzung')}"
                matches = matcher.hybrid_search(query)
                if matches:
                    st.write("Matching Companies in Database:")
                    for m in matches:
                        st.info(f"**{m['name']}** - {m['industry']} ({m['state']})")
                        st.write(m['summary'])
                else:
                    st.write("No matching companies found in database.")

        if st.button("Suggest Research Topics"):
            topics = matcher.suggest_research_topics(st.session_state.last_call)
            st.write("Suggested Topics:")
            for t in topics:
                st.write(f"- {t}")

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
