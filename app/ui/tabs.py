import streamlit as st
import os
import urllib.parse
from app.services.scraper_service import ScraperService
from app.services.analyzer_service import AnalyzerService
from app.utils.translations import translate
from app.utils.file_utils import get_file_age_days
from app.models.models import ResearchCallModel


def render_summarization_tab(llm_service, summaries_dir, parse_md_to_result):
    st.header(translate("research_call_analysis", st.session_state.lang))

    os.makedirs(summaries_dir, exist_ok=True)
    saved_files = sorted([f for f in os.listdir(summaries_dir) if f.endswith(".md")])

    if "last_call" not in st.session_state and saved_files:
        first_file = saved_files[0]
        try:
            with open(
                os.path.join(summaries_dir, first_file), "r", encoding="utf-8"
            ) as f:
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
        help="Paste the URL of a research funding call to analyze its content.",
    )

    if st.button(translate("analyze_call_button", st.session_state.lang)):
        scraper = ScraperService()
        analyzer = AnalyzerService(llm_service)
        with st.status("Fetching and analyzing...") as status:
            text_result = scraper.fetch_page_content(call_url)
            if text_result:
                try:
                    result = analyzer.analyze_research_call(
                        text_result["text"],
                        url=call_url,
                        status_callback=lambda msg: status.update(label=msg),
                    )
                    if result:
                        status.update(label="Analysis Complete!", state="complete")
                        st.session_state.last_call = result
                    else:
                        status.update(
                            label="Failed to analyze the call.", state="error"
                        )
                        st.error(
                            "Failed to analyze the call: Structured data extraction returned no result."
                        )
                except Exception as e:
                    status.update(label="Analysis Failed.", state="error")
                    st.error(f"Error analyzing research call: {str(e)}")
            else:
                status.update(label="Failed to fetch URL.", state="error")
                st.error("Failed to fetch the URL content.")

    col_load1, col_load2 = st.columns([3, 1])
    with col_load1:
        default_idx = 0
        if (
            "current_selected_file" in st.session_state
            and st.session_state.current_selected_file in saved_files
        ):
            default_idx = saved_files.index(st.session_state.current_selected_file)

        st.selectbox(
            translate("saved_summaries", st.session_state.lang),
            saved_files,
            index=default_idx,
            label_visibility="collapsed",
            key="summary_selector",
            on_change=load_selected_summary,
        )

    if "last_call" in st.session_state:
        result = st.session_state.last_call
        # Convert to ResearchCallModel if it's still a dict (from older cache)
        if isinstance(result, dict):
            try:
                result = ResearchCallModel.model_validate(result)
                st.session_state.last_call = result
            except Exception:
                pass

        current_file = st.session_state.get("current_selected_file", "")
        age_str = ""
        if current_file:
            age_days = get_file_age_days(os.path.join(summaries_dir, current_file))
            age_str = (
                f" ({translate('age_days', st.session_state.lang, days=age_days)})"
            )

        thema = (
            result.thema
            if isinstance(result, ResearchCallModel)
            else result.get("Thema", "N/A")
        )
        st.info(
            f"{translate('active_call', st.session_state.lang)} **{thema}**{age_str}"
        )
        st.subheader(f"Analysis: {thema}")

        beschreibung = (
            result.beschreibung
            if isinstance(result, ResearchCallModel)
            else result.get("Beschreibung", "No description available.")
        )
        st.markdown(beschreibung)

        st.write(f"### {translate('metadata', st.session_state.lang)}")
        col1, col2 = st.columns(2)

        if isinstance(result, ResearchCallModel):
            with col1:
                st.write(f"**Thema:** {result.thema}")
                st.write(f"**Zielsetzung:** {result.zielsetzung}")
                st.write(f"**Deadline:** {result.deadline}")
                st.write(f"**Sitz der Organisation:** {result.sitz_der_organisation}")
            with col2:
                st.write(f"**Budget:** {result.budget}")
                st.write(f"**Laufzeit:** {result.laufzeit}")
                st.write(f"**Prozess:** {result.einstufig_zweistufig}")
                st.write(f"**Link:** {result.link}")
            st.write(f"**Partner:** {result.anzahl_projektpartner}")
            st.write(f"**Antragsberechtigt:** {result.antragsberechtigt}")
            st.write(
                f"**Antragsberechtigt_Details:** {result.antragsberechtigt_details}"
            )
            if result.andere_metadaten:
                st.write(f"**Andere Metadaten:** {result.andere_metadaten}")
        else:
            with col1:
                st.write(f"**Thema:** {result.get('Thema')}")
                st.write(f"**Zielsetzung:** {result.get('Zielsetzung')}")
                st.write(f"**Deadline:** {result.get('Deadline')}")
                st.write(
                    f"**Sitz der Organisation:** {result.get('Sitz_der_Organisation', 'N/A')}"
                )
            with col2:
                st.write(f"**Budget:** {result.get('Budget')}")
                st.write(f"**Laufzeit:** {result.get('Laufzeit')}")
                st.write(f"**Prozess:** {result.get('Einstufig_Zweistufig')}")
                st.write(f"**Link:** {result.get('Link')}")
            st.write(f"**Partner:** {result.get('Anzahl_Projektpartner')}")
            st.write(f"**Antragsberechtigt:** {result.get('Antragsberechtigt', 'N/A')}")
            st.write(
                f"**Antragsberechtigt_Details:** {result.get('Antragsberechtigt_Details', 'N/A')}"
            )
            if result.get("Andere_Metadaten"):
                st.write(f"**Andere Metadaten:** {result.get('Andere_Metadaten')}")

        st.divider()
        st.write(f"### {translate('tools', st.session_state.lang)}")

        if isinstance(result, ResearchCallModel):
            summary_text = f"""Zusammenfassung der Ausschreibung: {result.thema}
Link: {result.link}

{result.beschreibung}

### Metadaten
- Thema: {result.thema}
- Zielsetzung: {result.zielsetzung}
- Deadline: {result.deadline}
- Sitz der Organisation: {result.sitz_der_organisation}
- Budget: {result.budget}
- Laufzeit: {result.laufzeit}
- Prozess: {result.einstufig_zweistufig}
- Partner: {result.anzahl_projektpartner}
- Antragsberechtigt: {result.antragsberechtigt}
- Antragsberechtigt_Details: {result.antragsberechtigt_details}
"""
        else:
            summary_text = f"""Zusammenfassung der Ausschreibung: {result.get("Thema")}
Link: {result.get("Link")}

{result.get("Beschreibung")}

### Metadaten
- Thema: {result.get("Thema")}
- Zielsetzung: {result.get("Zielsetzung")}
- Deadline: {result.get("Deadline")}
- Sitz der Organisation: {result.get("Sitz_der_Organisation")}
- Budget: {result.get("Budget")}
- Laufzeit: {result.get("Laufzeit")}
- Prozess: {result.get("Einstufig_Zweistufig")}
- Partner: {result.get("Anzahl_Projektpartner")}
- Antragsberechtigt: {result.get("Antragsberechtigt")}
- Antragsberechtigt_Details: {result.get("Antragsberechtigt_Details")}
"""
        st.subheader(translate("save_and_copy", st.session_state.lang))

        if st.button(translate("save_button", st.session_state.lang)):
            filename = f"{thema[:50]}.md".replace(" ", "_").replace("/", "_")
            filepath = os.path.join(summaries_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(summary_text)
            st.success(f"Gespeichert als {filename}")
            st.rerun()

        st.divider()
        st.code(summary_text, language="markdown")

        st.subheader("Versenden")
        email_body = f'Hallo ...,\n\nich habe die Ausschreibung "{thema}" analysieren lassen. Hier ist die Zusammenfassung:\n\n{summary_text}'
        subject = f"Zusammenfassung der Ausschreibung: {thema}"
        mailto_link = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(email_body)}"
        st.markdown(
            f'<a href="{mailto_link}" target="_blank" style="text-decoration: none;"><button style="background-color: #f63366; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer;">📧 Als Mail senden</button></a>',
            unsafe_allow_html=True,
        )
