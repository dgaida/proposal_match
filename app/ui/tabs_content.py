import json
import os

import pandas as pd
import pydeck as pdk
import streamlit as st

from app.models.models import ProposalModel, ResearchCallModel
from app.services.fit_service import FITService
from app.services.indexing_service import IndexingService
from app.services.linkedin_service import LinkedInService
from app.services.matching_service import MatchingService
from app.utils.file_utils import get_file_age_days
from app.utils.geo_utils import get_coordinates
from app.utils.translations import translate


def render_fit_tab(llm_service, fit_username, fit_password):
    st.header(translate("fit_search_title", st.session_state.lang))

    fit_cache_path = "data/fit_cache.json"
    if os.path.exists(fit_cache_path):
        age_days = get_file_age_days(fit_cache_path)
        st.info(
            f"{translate('tab_fit', st.session_state.lang)}: {translate('age_days', st.session_state.lang, days=age_days)}"
        )

    fit_query = st.text_input(
        translate("tab_fit", st.session_state.lang),
        placeholder="Künstliche Intelligenz",
        help="Enter search terms to find research calls in the FIT database.",
    )
    if st.button(translate("search_fit_button", st.session_state.lang)):
        if fit_username and fit_password:
            fit_service = FITService(llm_service)
            with st.status("Initializing FIT Search...") as status:
                if fit_service.login(
                    fit_username,
                    fit_password,
                    status_callback=lambda msg: status.update(label=msg),
                ):
                    results = fit_service.search_calls(
                        fit_query, status_callback=lambda msg: status.update(label=msg)
                    )
                    summary = fit_service.summarize_results(
                        results, status_callback=lambda msg: status.update(label=msg)
                    )

                    st.session_state.fit_results = {
                        "results": results,
                        "summary": summary,
                    }

                    os.makedirs("data", exist_ok=True)
                    with open("data/fit_cache.json", "w", encoding="utf-8") as f:
                        json.dump(
                            st.session_state.fit_results,
                            f,
                            ensure_ascii=False,
                            indent=4,
                        )

                    status.update(
                        label="Search and Analysis Complete!", state="complete"
                    )
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


def render_indexing_tab(llm_service, db_manager, vector_store):
    st.header(translate("company_indexing_title", st.session_state.lang))
    st.write(translate("company_indexing_desc", st.session_state.lang))
    company_links_input = st.text_area(
        translate("enter_company_links", st.session_state.lang),
        placeholder="https://company-a.com\nhttps://company-b.de",
        help=translate("company_links_help", st.session_state.lang),
    )
    uploaded_file = st.file_uploader(
        translate("upload_links_file", st.session_state.lang),
        type=["txt"],
        help=translate("upload_links_help", st.session_state.lang),
    )

    if st.button(translate("index_companies_button", st.session_state.lang)):
        links = []
        if company_links_input:
            links.extend(
                [
                    link_item.strip()
                    for link_item in company_links_input.split("\n")
                    if link_item.strip()
                ]
            )
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8")
            links.extend(
                [
                    link_item.strip()
                    for link_item in content.split("\n")
                    if link_item.strip()
                ]
            )

        if links:
            indexer = IndexingService(llm_service, db_manager, vector_store)
            progress_bar = st.progress(0)
            for i, link in enumerate(links):
                with st.status(
                    translate("indexing_status", st.session_state.lang, link=link)
                ):
                    indexer.index_companies_from_links([link])
                progress_bar.progress((i + 1) / len(links))
            st.success(translate("indexing_complete", st.session_state.lang))
        else:
            st.warning(translate("provide_links_warning", st.session_state.lang))

    st.divider()
    st.write(f"### {translate('recursive_folder_indexing', st.session_state.lang)}")
    folder_path = st.text_input(
        translate("enter_folder_path", st.session_state.lang),
        placeholder="/path/to/your/links/folder",
        help=translate("folder_path_help", st.session_state.lang),
    )
    folder_limit = st.number_input(
        translate("folder_indexing_limit", st.session_state.lang),
        min_value=1,
        value=25,
        step=1,
        help=translate("folder_limit_help", st.session_state.lang),
    )
    if st.button(translate("index_from_folder_button", st.session_state.lang)):
        if folder_path and os.path.exists(folder_path):
            indexer = IndexingService(llm_service, db_manager, vector_store)
            with st.status(
                translate("scanning_folder", st.session_state.lang, path=folder_path)
            ) as status:
                indexed = indexer.index_from_folder(
                    folder_path,
                    limit=folder_limit,
                    status_callback=lambda msg: status.update(label=msg),
                )
                status.update(
                    label=translate(
                        "folder_indexed_count",
                        st.session_state.lang,
                        count=len(indexed),
                    ),
                    state="complete",
                )
            st.success(f"Successfully indexed {len(indexed)} companies from folder.")
            if indexed:
                with st.expander("Show indexed companies/URLs"):
                    for url in indexed:
                        st.write(f"- {url}")
        else:
            st.error(translate("invalid_folder", st.session_state.lang))


def render_matching_tab(llm_service, db_manager, vector_store, parse_md_to_result):
    st.header(translate("matching_title", st.session_state.lang))

    if "current_matches" not in st.session_state:
        st.session_state.current_matches = []
    if "current_topics" not in st.session_state:
        st.session_state.current_topics = []
    if "last_queries" not in st.session_state:
        st.session_state.last_queries = []
    if "current_proposals" not in st.session_state:
        st.session_state.current_proposals = []
    if "current_call_name" not in st.session_state:
        st.session_state.current_call_name = ""

    search_mode = st.radio(
        translate("search_mode", st.session_state.lang),
        [
            translate("auto_matching", st.session_state.lang),
            translate("manual_matching", st.session_state.lang),
        ],
        help=translate("search_mode_help", st.session_state.lang),
    )

    matcher = MatchingService(llm_service, db_manager, vector_store)
    current_call_data = None
    call_name = "manual_search"

    if search_mode == translate("auto_matching", st.session_state.lang):
        summaries_dir = "data/summaries"
        os.makedirs(summaries_dir, exist_ok=True)
        saved_calls = [f for f in os.listdir(summaries_dir) if f.endswith(".md")]
        selected_call_file = st.selectbox(
            translate("saved_summaries", st.session_state.lang), saved_calls
        )

        if selected_call_file:
            call_name = selected_call_file.replace(".md", "")
            if st.session_state.current_call_name != call_name:
                st.session_state.current_call_name = call_name
                st.session_state.current_proposals = []
                st.session_state.current_topics = []
                st.session_state.current_matches = []
                st.session_state.last_queries = []

            with open(
                os.path.join(summaries_dir, selected_call_file), "r", encoding="utf-8"
            ) as f:
                current_call_data = parse_md_to_result(f.read())
                # Normalize to ResearchCallModel if possible
                if isinstance(current_call_data, dict):
                    try:
                        current_call_data = ResearchCallModel.model_validate(
                            current_call_data
                        )
                    except Exception:
                        pass

            thema = (
                current_call_data.thema
                if isinstance(current_call_data, ResearchCallModel)
                else current_call_data.get("Thema")
            )
            st.info(f"{translate('active_call', st.session_state.lang)} **{thema}**")

            proposals_dir = "data/proposals"
            os.makedirs(proposals_dir, exist_ok=True)
            proposal_cache_path = os.path.join(
                proposals_dir, f"{call_name}_proposals.json"
            )
            if (
                os.path.exists(proposal_cache_path)
                and not st.session_state.current_proposals
            ):
                try:
                    with open(proposal_cache_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        st.session_state.current_proposals = [
                            ProposalModel.model_validate(p) for p in data
                        ]
                except Exception:
                    pass
    else:
        manual_query = st.text_input(
            translate("search_query_label", st.session_state.lang),
            placeholder="z.B. KI im Maschinenbau",
            help=translate("search_query_help", st.session_state.lang),
        )

    st.subheader(translate("filters", st.session_state.lang))
    companies = db_manager.get_all_companies()
    countries = sorted({c.country for c in companies if c.country})
    states = sorted({c.state for c in companies if c.state})

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        default_country_index = 0
        sitz = ""
        if current_call_data:
            sitz = (
                (
                    current_call_data.sitz_der_organisation
                    if isinstance(current_call_data, ResearchCallModel)
                    else current_call_data.get("Sitz_der_Organisation", "")
                )
                .strip()
                .lower()
            )
        if sitz == "deutschland" and "Deutschland" in countries:
            default_country_index = countries.index("Deutschland") + 1
        country_filter = st.selectbox(
            translate("filter_country", st.session_state.lang),
            [translate("all_option", st.session_state.lang)] + countries,
            index=default_country_index,
            key="hybrid_country_filter",
        )
    with col_f2:
        state_filter = st.selectbox(
            translate("filter_state", st.session_state.lang),
            [translate("all_option", st.session_state.lang)] + states,
            index=0,
            key="hybrid_state_filter",
        )
    with col_f3:
        org_type_filter = st.selectbox(
            translate("filter_org_type", st.session_state.lang),
            [
                translate("all_option", st.session_state.lang),
                "Unternehmen",
                "Forschungseinrichtung",
                "Hochschule",
                "KMU",
            ],
            key="hybrid_org_filter",
        )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(translate("find_organisations_button", st.session_state.lang)):
            with st.spinner(translate("search_running", st.session_state.lang)):
                queries = []
                if (
                    search_mode == translate("auto_matching", st.session_state.lang)
                    and current_call_data
                ):
                    queries_dir = "data/queries"
                    os.makedirs(queries_dir, exist_ok=True)
                    query_cache_path = os.path.join(
                        queries_dir, f"{call_name}_multiple.json"
                    )
                    if os.path.exists(query_cache_path):
                        with open(query_cache_path, "r", encoding="utf-8") as f:
                            queries = json.load(f)
                    else:
                        call_json = (
                            current_call_data.model_dump()
                            if isinstance(current_call_data, ResearchCallModel)
                            else current_call_data
                        )
                        queries = matcher.generate_multiple_matching_queries(
                            call_json, n=5
                        )
                        with open(query_cache_path, "w", encoding="utf-8") as f:
                            json.dump(queries, f, ensure_ascii=False)
                elif (
                    search_mode == translate("manual_matching", st.session_state.lang)
                    and manual_query
                ):
                    optimized_query = matcher.rephrase_query(manual_query)
                    queries = matcher.generate_multiple_matching_queries(
                        optimized_query, n=5
                    )
                    if not current_call_data:
                        current_call_data = ResearchCallModel(
                            Thema=manual_query,
                            Beschreibung=f"Manuelle Suche nach: {manual_query}",
                        )

                if queries:
                    st.session_state.last_queries = queries
                    filters = {}
                    all_opt = translate("all_option", st.session_state.lang)
                    if country_filter != all_opt:
                        filters["country"] = country_filter
                    if state_filter != all_opt:
                        filters["state"] = state_filter
                    if org_type_filter != all_opt:
                        if org_type_filter == "KMU":
                            filters["org_type"] = "Unternehmen"
                            filters["kmu_status"] = True
                        else:
                            filters["org_type"] = org_type_filter

                    all_matches_dict = {}
                    for q in queries:
                        query_matches = matcher.hybrid_search(
                            q, filters=filters, limit=10
                        )
                        for m in query_matches:
                            url = m.url
                            if (
                                url not in all_matches_dict
                                or m.relevance > all_matches_dict[url].relevance
                            ):
                                all_matches_dict[url] = m

                    matches = sorted(
                        all_matches_dict.values(),
                        key=lambda x: x.relevance,
                        reverse=True,
                    )
                    if matches:
                        if current_call_data:
                            matches = matcher.generate_match_justification(
                                current_call_data, matches[:10]
                            )
                        st.session_state.current_matches = matches
                    else:
                        st.session_state.current_matches = []
                        st.warning(
                            "Keine passenden Organisationen in der Datenbank gefunden."
                        )

    with col_btn2:
        if st.button(translate("suggest_topics_button", st.session_state.lang)):
            if not current_call_data and search_mode == translate(
                "manual_matching", st.session_state.lang
            ):
                current_call_data = ResearchCallModel(
                    Thema=manual_query,
                    Beschreibung=f"Manuelle Suche nach: {manual_query}",
                )

            if current_call_data:
                with st.status(
                    translate("generating_suggestions", st.session_state.lang)
                ) as status:
                    proposals = matcher.generate_detailed_proposals(
                        current_call_data,
                        user_context=st.session_state.get("user_context", ""),
                        matched_companies=st.session_state.current_matches,
                        status_callback=lambda msg: status.update(label=msg),
                    )
                    st.session_state.current_proposals = proposals
                    if search_mode == translate("auto_matching", st.session_state.lang):
                        proposals_dir = "data/proposals"
                        os.makedirs(proposals_dir, exist_ok=True)
                        proposal_cache_path = os.path.join(
                            proposals_dir, f"{call_name}_proposals.json"
                        )
                        with open(proposal_cache_path, "w", encoding="utf-8") as f:
                            json.dump(
                                [p.model_dump() for p in proposals],
                                f,
                                ensure_ascii=False,
                                indent=4,
                            )
                    status.update(label="Vorschläge generiert!", state="complete")
            else:
                st.warning(
                    "Bitte wählen Sie einen Call aus oder geben Sie einen Suchbegriff für den Kontext an."
                )

    if st.session_state.last_queries:
        st.write(f"### {translate('used_queries', st.session_state.lang)}")
        for q in st.session_state.last_queries:
            st.info(q)

    if st.session_state.current_matches:
        st.write(f"### {translate('matching_title', st.session_state.lang)}:")
        for m in st.session_state.current_matches:
            relevance_pct = f"{int(m.relevance * 100)}%"
            with st.expander(
                f"**{m.name}** - Relevance: {relevance_pct} - {m.industry or 'N/A'} ({m.country or 'N/A'})"
            ):
                if m.justification:
                    st.write(
                        f"**{translate('justification', st.session_state.lang)}:** {m.justification}"
                    )
                st.write(
                    f"**{translate('summary', st.session_state.lang)}:** {m.summary}"
                )
                st.divider()
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(
                        f"**{translate('website', st.session_state.lang)}:** [{m.url}]({m.url})"
                    )
                    st.write(
                        f"**{translate('type', st.session_state.lang)}:** {m.org_type or 'N/A'}"
                    )
                    st.write(
                        f"**{translate('city', st.session_state.lang)}:** {m.city or 'N/A'}"
                    )
                with col_info2:
                    st.write(
                        f"**{translate('employees', st.session_state.lang)}:** {m.employees_count or 'N/A'}"
                    )
                    st.write(
                        f"**{translate('sme_status', st.session_state.lang)}:** {'Ja' if m.kmu_status else 'Nein'}"
                    )

    if st.session_state.current_proposals:
        st.write(f"### {translate('suggested_research_topics', st.session_state.lang)}")
        for prop in st.session_state.current_proposals:
            with st.expander(f"**{prop.title}**"):
                st.write(prop.description)
                st.write(
                    f"#### {translate('existing_partners', st.session_state.lang)}"
                )
                for p in prop.existing_partners:
                    st.write(f"- **{p.name}**: {p.role}")
                if prop.newly_found_partners:
                    st.write(
                        f"#### {translate('newly_found_partners', st.session_state.lang)}"
                    )
                    for p in prop.newly_found_partners:
                        relevance_pct = f"{int(p.relevance * 100)}%"
                        st.write(
                            f"- **{p.name}** ({p.city}, {p.org_type}) - Relevance: {relevance_pct}"
                        )
                        st.info(p.summary)
                if prop.missing_partners_search:
                    st.write(
                        f"#### {translate('missing_partners', st.session_state.lang)}"
                    )
                    for mp in prop.missing_partners_search:
                        st.write(f"- {mp.type_description} (*{mp.intended_role}*)")

    st.divider()
    st.subheader(translate("discover_internet", st.session_state.lang))
    internet_topic = st.text_input(
        translate("topic_internet_search", st.session_state.lang),
        placeholder="Innovative startups in robotics Germany",
    )
    if st.button(translate("search_internet_button", st.session_state.lang)):
        with st.spinner(translate("search_running", st.session_state.lang)):
            web_results = matcher.search_internet_for_companies(internet_topic)
            for res in web_results:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**[{res['name']}]({res['url']})**")
                    st.write(res["snippet"])
                with col2:
                    if st.button(
                        translate("index_this_company", st.session_state.lang),
                        key=res["url"],
                    ):
                        indexer = IndexingService(llm_service, db_manager, vector_store)
                        indexer.index_companies_from_links([res["url"]])
                        st.success("Indexed!")


def render_linkedin_tab(llm_service, li_username, li_password):
    st.header(translate("linkedin_matching_title", st.session_state.lang))
    st.warning(translate("linkedin_notice", st.session_state.lang))
    if li_username and li_password:
        li_service = LinkedInService(llm_service, li_username, li_password)
        li_limit = st.number_input(
            translate("li_contacts_limit", st.session_state.lang),
            min_value=1,
            value=20,
            step=1,
        )
        if st.button(translate("fetch_contacts_button", st.session_state.lang)):
            if "last_call" in st.session_state:
                with st.status(
                    translate("li_processing", st.session_state.lang)
                ) as status:
                    contacts = li_service.get_first_degree_contacts(
                        limit=li_limit,
                        status_callback=lambda msg: status.update(label=msg),
                    )
                    if contacts:
                        result = li_service.find_matching_contacts_for_call(
                            contacts,
                            st.session_state.last_call,
                            status_callback=lambda msg: status.update(label=msg),
                        )
                        matches = result.get("matches", [])
                        identified_names = result.get("identified_names", [])
                        criteria = result.get("criteria", "")
                        if identified_names:
                            status.update(
                                label=translate(
                                    "llm_identified_matches",
                                    st.session_state.lang,
                                    count=len(identified_names),
                                ),
                                state="complete",
                            )
                            st.subheader(
                                translate("matching_criteria", st.session_state.lang)
                            )
                            st.write(criteria)
                            st.subheader(
                                translate(
                                    "contacts_identified_llm", st.session_state.lang
                                )
                            )
                            st.write(", ".join(identified_names))
                            if matches:
                                st.subheader(
                                    translate(
                                        "final_matching_contacts", st.session_state.lang
                                    )
                                )
                                for contact in matches:
                                    c_name = f"{contact.get('firstName')} {contact.get('lastName')}"
                                    st.write(
                                        f"**{c_name}** - {contact.get('occupation')}"
                                    )
                                    if st.button(
                                        f"Generate Message for {contact.get('firstName')}",
                                        key=contact.get("public_id"),
                                    ):
                                        msg = li_service.generate_outreach_message(
                                            c_name,
                                            "his/her company",
                                            st.session_state.last_call,
                                        )
                                        st.text_area("Message:", value=msg, height=200)
                            else:
                                st.info(
                                    translate(
                                        "no_matching_contacts_detailed",
                                        st.session_state.lang,
                                    )
                                )
                        else:
                            status.update(
                                label=translate(
                                    "no_matches_found", st.session_state.lang
                                ),
                                state="error",
                            )
                            st.info(
                                translate(
                                    "no_matching_contacts_llm", st.session_state.lang
                                )
                            )
                    else:
                        status.update(
                            label=translate("no_contacts_found", st.session_state.lang),
                            state="error",
                        )
                        st.info(
                            translate("no_li_contacts_found", st.session_state.lang)
                        )
            else:
                st.warning(translate("analyze_first_warn", st.session_state.lang))
    else:
        st.warning(translate("provide_li_creds", st.session_state.lang))


def render_database_tab(db_manager):
    st.header(translate("database_title", st.session_state.lang))
    if st.button(translate("refresh_db_button", st.session_state.lang)):
        removed = db_manager.deduplicate_companies()
        if removed > 0:
            st.success(
                translate(
                    "all_duplicates_removed", st.session_state.lang, count=removed
                )
            )
        else:
            st.info(translate("no_duplicates_found", st.session_state.lang))
        st.rerun()

    companies = db_manager.get_all_companies()
    if companies:
        st.subheader(translate("filter_and_search", st.session_state.lang))
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            name_filter = st.text_input(
                translate("search_name", st.session_state.lang),
                placeholder="Unternehmen A",
                key="db_name_filter",
            )
        with col_f2:
            countries = sorted({c.country for c in companies if c.country})
            country_filter = st.selectbox(
                translate("filter_country", st.session_state.lang),
                [translate("all_option", st.session_state.lang)] + countries,
                key="db_country_filter",
            )
        with col_f3:
            states = sorted({c.state for c in companies if c.state})
            state_filter = st.selectbox(
                translate("filter_state", st.session_state.lang),
                [translate("all_option", st.session_state.lang)] + states,
                key="db_state_filter",
            )
        with col_f4:
            org_types = sorted({c.org_type for c in companies if c.org_type})
            org_filter_options = [
                translate("all_option", st.session_state.lang)
            ] + org_types
            if "KMU" not in org_filter_options:
                org_filter_options.append("KMU")
            org_type_filter = st.selectbox(
                translate("filter_org_type", st.session_state.lang),
                org_filter_options,
                key="db_org_type_filter",
            )

        data = []
        all_opt = translate("all_option", st.session_state.lang)
        selected_urls = st.session_state.get("last_selected_urls", [])

        for c in companies:
            if name_filter and name_filter.lower() not in (c.name or "").lower():
                continue
            if country_filter != all_opt and c.country != country_filter:
                continue
            if state_filter != all_opt and c.state != state_filter:
                continue
            if org_type_filter != all_opt:
                if org_type_filter == "KMU":
                    if c.org_type != "Unternehmen" or not c.kmu_status:
                        continue
                elif c.org_type != org_type_filter:
                    continue

            data.append(
                {
                    "Select": c.url in selected_urls,
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
                    "Products": c.products,
                }
            )
        data.sort(key=lambda x: (x.get("Name") or "").lower())
        st.write(translate("displayed_entries", st.session_state.lang, count=len(data)))

        if data:
            map_data = []
            selected_urls = st.session_state.get("last_selected_urls", [])
            for item in data:
                state = (item.get("State") or "").lower()
                if state not in [
                    "nrw",
                    "nordrhein-westfalen",
                    "north rhine-westphalia",
                ]:
                    continue
                coords = get_coordinates(
                    item.get("City"),
                    item.get("Land") or "Germany",
                    only_from_cache=True,
                )
                if coords:
                    color = [246, 51, 102, 200]
                    radius = 6
                    if item.get("URL") in selected_urls:
                        color = [50, 205, 50, 255]
                        radius = 10
                    map_data.append(
                        {
                            "name": item.get("Name"),
                            "url": item.get("URL"),
                            "lat": coords[0],
                            "lon": coords[1],
                            "color": color,
                            "radius_pixels": radius,
                        }
                    )

            if map_data:
                df_map = pd.DataFrame(map_data)
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    df_map,
                    id="company-layer",
                    get_position="[lon, lat]",
                    get_color="color",
                    radius_units="pixels",
                    get_radius="radius_pixels",
                    pickable=True,
                )
                event = st.pydeck_chart(
                    pdk.Deck(
                        layers=[layer],
                        initial_view_state=pdk.ViewState(
                            latitude=51.48, longitude=7.55, zoom=6
                        ),
                        tooltip={"text": "{name}"},
                    ),
                    on_select="rerun",
                    selection_mode="single-object",
                    key="db_map",
                )
                if (
                    event
                    and "selection" in event
                    and event["selection"]["objects"].get("company-layer")
                ):
                    clicked_url = event["selection"]["objects"]["company-layer"][0].get(
                        "url"
                    )
                    if clicked_url and clicked_url not in st.session_state.get(
                        "last_selected_urls", []
                    ):
                        st.session_state.last_selected_urls = [clicked_url]
                        st.rerun()

        edited_data = st.data_editor(
            data, width="stretch", num_rows="dynamic", key="db_editor"
        )
        if edited_data is not None:
            new_selected_urls = [
                row.get("URL")
                for row in edited_data
                if isinstance(row, dict) and row.get("Select")
            ]
            if new_selected_urls != st.session_state.get("last_selected_urls", []):
                st.session_state.last_selected_urls = new_selected_urls
                st.rerun()

        db_edits = st.session_state.get("db_editor", {})
        if (
            db_edits.get("edited_rows")
            or db_edits.get("added_rows")
            or db_edits.get("deleted_rows")
        ):
            update_list = [
                {
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
                    "products": row.get("Products"),
                }
                for row in edited_data
            ]
            try:
                db_manager.update_companies(update_list)
                st.toast(translate("auto_saved", st.session_state.lang))
            except Exception as e:
                st.error(translate("save_error", st.session_state.lang, error=e))

        st.subheader(translate("detailed_profiles", st.session_state.lang))
        sel_urls = (
            [
                row.get("URL")
                for row in edited_data
                if isinstance(row, dict) and row.get("Select") and row.get("URL")
            ]
            if isinstance(edited_data, list)
            else []
        )
        for c in companies:
            if c.url in sel_urls:
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
                    st.write(f"**{translate('summary', st.session_state.lang)}:**")
                    st.write(c.summary)
                    st.write("**Products/Services:**")
                    st.write(c.products)
    else:
        st.info(translate("no_companies_indexed", st.session_state.lang))
