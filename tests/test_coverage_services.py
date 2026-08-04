import os
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from typing import Dict, Any, List

from app.services.analyzer_service import AnalyzerService
from app.services.fit_service import FITService
from app.services.indexing_service import IndexingService
from app.services.linkedin_service import LinkedInService
from app.services.llm_service import LLMService
from app.services.matching_service import MatchingService
from app.services.scraper_service import ScraperService

from app.models.models import ResearchCallModel, CompanyModel, MatchResultModel, ProposalModel
from app.utils.db_manager import DBManager, Company
from app.utils.vector_store import VectorStore


# ==========================================
# 1. analyzer_service.py tests
# ==========================================
def test_analyzer_service_success():
    mock_llm = MagicMock()
    # Return structured JSON matching ResearchCallModel
    mock_llm.extract_structured_data.return_value = json.dumps({
        "Thema": "AI in Farming",
        "Zielsetzung": "Improve crop yield",
        "Deadline": "2026-06-30",
        "Sitz_der_Organisation": "Deutschland",
        "Einstufig_Zweistufig": "Einstufig",
        "Anzahl_Projektpartner": "3+",
        "Budget": "500k EUR",
        "Laufzeit": "3 years",
        "Antragsberechtigt": "Hochschulen, KMUs",
        "Antragsberechtigt_Details": "At least 1 SME required",
        "Andere_Metadaten": "None",
        "Link": "https://farming.org",
        "Beschreibung": "Detailed markdown description in German"
    })

    analyzer = AnalyzerService(mock_llm)
    res = analyzer.analyze_research_call("Some text about farming", url="https://farming.org")

    assert res is not None
    assert res.thema == "AI in Farming"
    assert res.deadline == "2026-06-30"
    mock_llm.extract_structured_data.assert_called_once()


def test_analyzer_service_json_parsing_failed():
    mock_llm = MagicMock()
    # Returns completely invalid json
    mock_llm.extract_structured_data.return_value = "invalid response from LLM"

    analyzer = AnalyzerService(mock_llm)
    res = analyzer.analyze_research_call("farming text")
    assert res is None


def test_analyzer_service_validation_failed():
    mock_llm = MagicMock()
    # Returns json that misses required field "Thema"
    mock_llm.extract_structured_data.return_value = json.dumps({
        "Zielsetzung": "no thema field here"
    })

    analyzer = AnalyzerService(mock_llm)
    res = analyzer.analyze_research_call("farming text")
    assert res is None


def test_analyzer_service_exception():
    mock_llm = MagicMock()
    mock_llm.extract_structured_data.side_effect = Exception("LLM crash")

    analyzer = AnalyzerService(mock_llm)
    with pytest.raises(Exception) as excinfo:
        analyzer.analyze_research_call("farming text")
    assert "LLM crash" in str(excinfo.value)


# ==========================================
# 2. fit_service.py tests
# ==========================================
def test_fit_service_login_success():
    mock_llm = MagicMock()
    fit = FITService(mock_llm)

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"access_token": "secret_token_123"}

        callback = MagicMock()
        res = fit.login("user", "pass", status_callback=callback)

        assert res is True
        callback.assert_called_with("Logging in to FIT Uni Kassel...")
        assert fit.client.headers.get("Authorization") == "Bearer secret_token_123"


def test_fit_service_login_failure():
    mock_llm = MagicMock()
    fit = FITService(mock_llm)

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=401, text="Unauthorized")
        res = fit.login("user", "bad_pass")
        assert res is False


def test_fit_service_login_exception():
    mock_llm = MagicMock()
    fit = FITService(mock_llm)

    with patch("httpx.Client.post", side_effect=Exception("Timeout")):
        res = fit.login("user", "pass")
        assert res is False


def test_fit_service_search_calls_empty():
    mock_llm = MagicMock()
    fit = FITService(mock_llm)

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = {"docs": []}

        res = fit.search_calls("AI query")
        assert res == []


def test_fit_service_search_calls_success_with_relevance_filtering():
    mock_llm = MagicMock()
    fit = FITService(mock_llm)

    docs = [
        {"title": "Call 0", "shortDescription": "Desc 0"},
        {"title": "Call 1", "shortDescription": "Desc 1"},
        {"title": "Call 2", "shortDescription": "Desc 2"},
    ]

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = {"docs": docs}

        # Mock LLM relevance filtering returning a JSON list of indices [0, 2]
        mock_llm.chat_completion.return_value = "[0, 2]"

        res = fit.search_calls("AI query")
        assert len(res) == 2
        assert res[0]["title"] == "Call 0"
        assert res[1]["title"] == "Call 2"


def test_fit_service_search_calls_fallback_filtering_parsing_failure():
    mock_llm = MagicMock()
    fit = FITService(mock_llm)

    docs = [{"title": f"Call {i}", "shortDescription": f"Desc {i}"} for i in range(15)]

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = {"docs": docs}

        # LLM returns invalid json list
        mock_llm.chat_completion.return_value = "invalid list"

        res = fit.search_calls("AI query")
        # should fallback to first 10
        assert len(res) == 10
        assert res[0]["title"] == "Call 0"


def test_fit_service_search_calls_fallback_filtering_exception():
    mock_llm = MagicMock()
    fit = FITService(mock_llm)

    docs = [{"title": f"Call {i}", "shortDescription": f"Desc {i}"} for i in range(12)]

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = {"docs": docs}

        # LLM raises exception
        mock_llm.chat_completion.side_effect = Exception("LLM failure")

        res = fit.search_calls("AI query")
        assert len(res) == 10


def test_fit_service_search_calls_http_exception():
    mock_llm = MagicMock()
    fit = FITService(mock_llm)

    with patch("httpx.Client.get", side_effect=Exception("HTTP error")):
        res = fit.search_calls("AI query")
        assert res == []


def test_fit_service_summarize_results():
    mock_llm = MagicMock()
    fit = FITService(mock_llm)

    # Empty
    assert fit.summarize_results([]) == "Keine relevanten Ergebnisse gefunden."

    # Non-empty
    mock_llm.chat_completion.return_value = "This is a German summary"
    res = fit.summarize_results([{"title": "Call 1", "description": "Desc 1"}])
    assert res == "This is a German summary"
    mock_llm.chat_completion.assert_called_once()


# ==========================================
# 3. indexing_service.py tests
# ==========================================
def test_indexing_service_from_links():
    mock_llm = MagicMock()
    mock_db = MagicMock()
    mock_vs = MagicMock()

    indexer = IndexingService(mock_llm, mock_db, mock_vs)

    # 1. Test when scraper returns None
    with patch.object(indexer.scraper_service, "fetch_page_content", return_value=None):
        assert indexer.index_companies_from_links(["http://comp1.com"]) == 0

    # 2. Test when final URL is already indexed
    scraper_res = {"text": "some html text", "final_url": "https://comp1.com/"}
    with patch.object(indexer.scraper_service, "fetch_page_content", return_value=scraper_res):
        mock_db.is_url_indexed.return_value = True
        assert indexer.index_companies_from_links(["http://comp1.com"]) == 0
        mock_db.is_url_indexed.assert_called_with("https://comp1.com")

    # 3. Test successful extraction and indexing
    mock_db.is_url_indexed.return_value = False
    mock_llm.extract_structured_data.return_value = json.dumps({
        "Name": "Company Alpha",
        "Land": "Germany",
        "Bundesland": "NRW",
        "Stadt": "Köln",
        "Organisationsart": "Unternehmen",
        "Anzahl_Mitarbeiter": 50,
        "KMU_Status": True,
        "Branche": "IT",
        "Bereits_aktiv_in_Forschungsprojekten": True,
        "Zusammenfassung": "Innovative IT company",
        "Produkte": "Software"
    })

    with patch.object(indexer.scraper_service, "fetch_page_content", return_value=scraper_res):
        assert indexer.index_companies_from_links(["http://comp1.com"]) == 1
        mock_db.add_company.assert_called_once()
        mock_vs.add_company_vector.assert_called_once_with(
            "https://comp1.com",
            "Company: Company Alpha. Innovative IT company Products: Software",
            mock_db.add_company.call_args[0][0]
        )


def test_indexing_service_extract_company_info_failures():
    mock_llm = MagicMock()
    indexer = IndexingService(mock_llm, MagicMock(), MagicMock())

    # LLM returns invalid json
    mock_llm.extract_structured_data.return_value = "not json"
    assert indexer._extract_company_info("text", "https://url.com") is None

    # LLM throws exception
    mock_llm.extract_structured_data.side_effect = Exception("LLM error")
    assert indexer._extract_company_info("text", "https://url.com") is None


def test_indexing_service_from_folder(tmp_path):
    mock_llm = MagicMock()
    mock_db = MagicMock()
    mock_vs = MagicMock()

    indexer = IndexingService(mock_llm, mock_db, mock_vs)

    # Folders does not exist
    assert indexer.index_from_folder("non_existing_dir") == []

    # Create temp folder with .url file
    folder = tmp_path / "urls"
    folder.mkdir()
    url_file = folder / "test.url"
    url_file.write_text("[InternetShortcut]\nURL=https://newcomp.com\n")

    # Create invalid .url file to trigger read error or regex mismatch
    bad_file = folder / "bad.url"
    bad_file.write_text("No URL field here")

    # DB mock returns existing company list
    c_existing = MagicMock()
    c_existing.url = "https://alreadyindexed.com"
    mock_db.get_all_companies.return_value = [c_existing]

    # Add already indexed .url file
    dup_file = folder / "dup.url"
    dup_file.write_text("URL=https://alreadyindexed.com\n")

    callback = MagicMock()

    with patch.object(indexer, "index_companies_from_links", return_value=1) as mock_index_links:
        res = indexer.index_from_folder(str(folder), limit=5, status_callback=callback)
        assert res == ["https://newcomp.com"]
        mock_index_links.assert_called_once_with(["https://newcomp.com"])
        callback.assert_any_call("Skipping already indexed or duplicate URL: https://alreadyindexed.com")


def test_indexing_service_extract_url_exception():
    indexer = IndexingService(MagicMock(), MagicMock(), MagicMock())
    # trigger open exception by mocking open to raise an error
    with patch("builtins.open", side_effect=IOError("Permission denied")):
        assert indexer._extract_url_from_file("some_file.url") is None


# ==========================================
# 4. linkedin_service.py tests
# ==========================================
def test_linkedin_service_init_failure():
    mock_llm = MagicMock()
    with patch("app.services.linkedin_service.Linkedin", side_effect=Exception("API error")):
        service = LinkedInService(mock_llm, "user", "pass")
        assert service.api is None


def test_linkedin_service_get_contacts():
    mock_llm = MagicMock()

    # 1. API not initialized
    service = LinkedInService(mock_llm)
    callback = MagicMock()
    assert service.get_first_degree_contacts(status_callback=callback) == []
    callback.assert_called_with("LinkedIn API not initialized. Check credentials.")

    # 2. Success path
    mock_api = MagicMock()
    connections = [
        {"firstName": "John", "lastName": "Doe", "occupation": "Researcher"},
        {"firstName": "Jane", "lastName": "Smith", "occupation": "CTO"},
    ]
    mock_api.search_people.return_value = connections

    with patch("app.services.linkedin_service.Linkedin", return_value=mock_api):
        service2 = LinkedInService(mock_llm, "user", "pass")
        assert service2.api is not None

        res = service2.get_first_degree_contacts(limit=10, status_callback=callback)
        assert res == connections
        mock_api.search_people.assert_called_once_with(network_depths=["F"], limit=10)

    # 3. Exception path
    mock_api.search_people.side_effect = Exception("Network timeout")
    with patch("app.services.linkedin_service.Linkedin", return_value=mock_api):
        service3 = LinkedInService(mock_llm, "user", "pass")
        res_fail = service3.get_first_degree_contacts()
        assert res_fail == []


def test_linkedin_service_generate_outreach():
    mock_llm = MagicMock()
    service = LinkedInService(mock_llm)

    mock_llm.chat_completion.return_value = "Dear John, let's collaborate..."

    call_data = {"Thema": "AI in healthcare"}
    msg = service.generate_outreach_message("John Doe", "Healthcare Inc", call_data)
    assert msg == "Dear John, let's collaborate..."
    mock_llm.chat_completion.assert_called_once()


def test_linkedin_service_find_matching_contacts():
    mock_llm = MagicMock()
    service = LinkedInService(mock_llm)

    contacts = [
        {"firstName": "John", "lastName": "Doe", "occupation": "AI Specialist"},
        {"firstName": "Jane", "lastName": "Smith", "occupation": "Mechanical Engineer"},
    ]

    # 1. Empty contacts
    assert service.find_matching_contacts_for_call([], {}) == {"matches": [], "identified_names": [], "criteria": ""}

    # 2. Match with Criteria parsing
    mock_llm.chat_completion.return_value = """
    Criteria: Looking for AI specialists.
    Names:
    - John Doe
    """
    callback = MagicMock()
    res = service.find_matching_contacts_for_call(contacts, {"Thema": "AI"}, status_callback=callback)
    assert res["matches"] == [contacts[0]]
    assert res["identified_names"] == ["John Doe"]
    assert res["criteria"] == "Looking for AI specialists."

    # 3. Fallback matching (no criteria in response)
    mock_llm.chat_completion.return_value = "- Jane Smith"
    res2 = service.find_matching_contacts_for_call(contacts, {"Thema": "Mechanical"})
    assert res2["matches"] == [contacts[1]]
    assert res2["criteria"] == "No criteria provided."

    # 4. Exception path
    mock_llm.chat_completion.side_effect = Exception("LLM disconnect")
    res3 = service.find_matching_contacts_for_call(contacts, {"Thema": "AI"})
    assert res3 == {"matches": [], "identified_names": [], "criteria": ""}


# ==========================================
# 5. llm_service.py tests
# ==========================================
def test_llm_service():
    # Test standard init
    with patch("app.services.llm_service.LLMClient") as MockLLMClient:
        service = LLMService(provider="openai", api_key="sk-test", llm_model="gpt-4o")
        assert service.provider == "openai"
        assert service.api_key == "sk-test"
        assert service.llm_model == "gpt-4o"
        assert os.environ.get("OPENAI_API_KEY") == "sk-test"
        MockLLMClient.assert_called_once_with(api_choice="openai", llm="gpt-4o", max_tokens=8192)

    # Test chat completion
    with patch("app.services.llm_service.LLMClient") as MockLLMClient:
        client_instance = MockLLMClient.return_value
        client_instance.chat_completion.return_value = "Hello back"

        service = LLMService(provider="groq")
        res = service.chat_completion([{"role": "user", "content": "Hello"}])
        assert res == "Hello back"
        client_instance.chat_completion.assert_called_once()

    # Test chat_with_fallback
    with patch("app.services.llm_service.LLMClient") as MockLLMClient:
        client_instance = MockLLMClient.return_value
        # Mock available providers
        with patch("os.getenv", side_effect=lambda key: "val" if key in ["OPENAI_API_KEY", "GROQ_API_KEY"] else None):
            service = LLMService(provider="openai")
            assert "groq" in service.available_providers

            # Scenario 1: First provider succeeds
            client_instance.chat_completion.return_value = "First success"
            assert service.chat_with_fallback([{"role": "user"}]) == "First success"

            # Scenario 2: First provider fails, second succeeds
            # chat_completion raises error on first call, returns "Second success" on second call
            client_instance.chat_completion.side_effect = [Exception("OpenAI rate limit"), "Second success"]
            callback = MagicMock()
            res = service.chat_with_fallback([{"role": "user"}], status_callback=callback)
            assert res == "Second success"
            callback.assert_any_call("Switching to Groq due to error...")

            # Scenario 3: All fail
            client_instance.chat_completion.side_effect = Exception("Connection error")
            with pytest.raises(Exception) as excinfo:
                service.chat_with_fallback([{"role": "user"}])
            assert "Connection error" in str(excinfo.value)


# ==========================================
# 6. matching_service.py tests
# ==========================================
def test_matching_service():
    mock_llm = MagicMock()
    mock_db = MagicMock()
    mock_vs = MagicMock()

    matcher = MatchingService(mock_llm, mock_db, mock_vs)

    # 1. suggest_research_topics
    mock_llm.chat_completion.return_value = "1. AI Drone\n2. Smart Irrigation"
    call_data = {"Thema": "Smart Farming"}
    matched_companies = [{"name": "C1", "industry": "Agriculture", "summary": "Does farming tech"}]

    res = matcher.suggest_research_topics(call_data, user_context="Research Center", matched_companies=matched_companies)
    assert len(res) == 2
    assert res[0] == "AI Drone"
    assert res[1] == "Smart Irrigation"

    # 2. generate_multiple_matching_queries
    mock_llm.chat_completion.return_value = "Query One\nQuery Two"
    queries = matcher.generate_multiple_matching_queries(call_data, n=2)
    assert queries == ["Query One", "Query Two"]

    # 3. rephrase_query
    mock_llm.chat_completion.return_value = "Rephrased semantic query"
    rephrased = matcher.rephrase_query("simple query")
    assert rephrased == "Rephrased semantic query"


def test_matching_service_hybrid_search():
    mock_llm = MagicMock()
    mock_db = MagicMock()
    mock_vs = MagicMock()

    matcher = MatchingService(mock_llm, mock_db, mock_vs)

    # Set up filters
    filters = {
        "state": "NRW",
        "country": "Germany",
        "org_type": "Unternehmen",
        "kmu_status": True
    }

    # Vector store results
    # Returns one ID with trailing slash, one without
    mock_vs.query_companies.return_value = {
        "ids": [["https://matching1.com", "https://matching2.com/"]],
        "distances": [[0.1, 0.4]]
    }

    # DB mock
    db_company_1 = Company(id=1, name="M1", url="https://matching1.com", state="NRW", country="Germany", org_type="Unternehmen", kmu_status=True)
    db_company_2 = Company(id=2, name="M2", url="https://matching2.com/", state="NRW", country="Germany", org_type="Unternehmen", kmu_status=True)

    session = MagicMock()
    mock_db.Session.return_value = session
    db_query_mock = session.query.return_value
    # mock .count() for logging
    db_query_mock.filter.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 2
    # mock .all() for retrieval
    db_query_mock.filter.return_value.all.return_value = [db_company_1, db_company_2]

    results = matcher.hybrid_search("Query text", filters=filters, keywords="IoT", limit=5)

    assert len(results) == 2
    assert results[0].name == "M1"
    assert results[0].relevance == 1.0 / (1.0 + 0.1)
    assert results[1].name == "M2"
    assert results[1].relevance == 1.0 / (1.0 + 0.4)

    # Verify vector store call received filters
    mock_vs.query_companies.assert_called_with(
        query_text="Query text",
        n_results=5,
        where={"$and": [
            {"state": {"$eq": "NRW"}},
            {"country": {"$eq": "Germany"}},
            {"org_type": {"$eq": "Unternehmen"}},
            {"kmu_status": {"$eq": True}}
        ]},
        where_document={"$contains": "IoT"}
    )


def test_matching_service_detailed_proposals():
    mock_llm = MagicMock()
    mock_db = MagicMock()
    mock_vs = MagicMock()

    matcher = MatchingService(mock_llm, mock_db, mock_vs)

    # Scenario 1: LLM returns invalid json list
    mock_llm.chat_completion.return_value = "invalid json list"
    assert matcher.generate_detailed_proposals({"Thema": "Smart Cities"}) == []

    # Scenario 2: Success path
    proposal_data = [
        {
            "title": "Smart Trash",
            "description": "Smart bins using IoT.",
            "existing_partners": [{"name": "SME Alpha", "role": "Hardware"}],
            "missing_partners_search": [
                {
                    "type_description": "Data analyst",
                    "filters": {"country": "Germany"},
                    "queries": ["Data analytics company"],
                    "keywords": "AI",
                    "intended_role": "Backend analytics"
                }
            ]
        }
    ]
    mock_llm.chat_completion.return_value = json.dumps(proposal_data)

    # Setup hybrid_search mocking inside matching service
    matched_company = MatchResultModel(
        name="Analyst Corp",
        url="https://analyst.com",
        relevance=0.8,
        state="NRW",
        city="Köln"
    )

    with patch.object(matcher, "hybrid_search", return_value=[matched_company]) as mock_hybrid:
        callback = MagicMock()
        res = matcher.generate_detailed_proposals(
            call_data=ResearchCallModel(Thema="IoT", Beschreibung="Detailed info"),
            user_context="University",
            matched_companies=[MatchResultModel(name="SME Alpha", url="https://alpha.com", relevance=0.9)],
            status_callback=callback
        )
        assert len(res) == 1
        assert res[0].title == "Smart Trash"
        assert res[0].newly_found_partners == [matched_company]
        mock_hybrid.assert_called_once_with(
            "Data analytics company",
            filters={"country": "Germany"},
            keywords="AI",
            limit=3
        )


def test_matching_service_generate_justification_and_internet_search():
    mock_llm = MagicMock()
    mock_db = MagicMock()
    mock_vs = MagicMock()

    matcher = MatchingService(mock_llm, mock_db, mock_vs)

    # Justification with empty
    assert matcher.generate_match_justification({}, []) == []

    # Justification success
    mock_llm.chat_completion.return_value = "Justification text"
    matched = [MatchResultModel(name="M1", url="https://m1.com", relevance=0.8)]
    res = matcher.generate_match_justification({"Thema": "Smart Cities"}, matched)
    assert res[0].justification == "Justification text"

    # Internet search
    # Mock LLM query generation
    mock_llm.chat_completion.return_value = "Query 1\nQuery 2"

    # Mock duckduckgo search
    mock_ddgs_instance = MagicMock()
    mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
    mock_ddgs_instance.text.return_value = [
        {"href": "https://newcompany.com", "title": "New Company Tech", "body": "We do innovative IoT solutions"}
    ]

    with patch("app.services.matching_service.DDGS", return_value=mock_ddgs_instance):
        web_results = matcher.search_internet_for_companies("IoT tech")
        assert len(web_results) == 1
        assert web_results[0]["url"] == "https://newcompany.com"
        assert web_results[0]["name"] == "New Company Tech"


# ==========================================
# 7. scraper_service.py tests
# ==========================================
def test_scraper_service():
    scraper = ScraperService()

    # 1. Success path
    html_content = """
    <html>
        <head><style>h1 {color: red;}</style></head>
        <body>
            <script>alert('hello');</script>
            <h1>Main Title</h1>
            <p>Some text content.</p>
        </body>
    </html>
    """
    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, content=html_content.encode("utf-8"), url="https://target.com/redirected")

        res = scraper.fetch_page_content("https://target.com")
        assert res is not None
        assert res["final_url"] == "https://target.com/redirected"
        assert "Main Title" in res["text"]
        assert "Some text content." in res["text"]
        # Script and style should be stripped
        assert "alert" not in res["text"]
        assert "color: red" not in res["text"]

    # 2. Exception/Failure path
    with patch("httpx.Client.get", side_effect=Exception("Connection refused")):
        res_fail = scraper.fetch_page_content("https://target.com")
        assert res_fail is None
