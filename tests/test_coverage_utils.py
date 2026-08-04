import os
import json
import time
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.utils.file_utils import get_file_age_days
from app.utils.fit_explorer import explore_fit
from app.utils.geo_utils import (
    get_coordinates,
    batch_geocode,
    load_cache,
    save_cache,
    CACHE_FILE,
    _geo_cache,
    _failed_keys,
    _nominatim_disabled,
)
import app.utils.geo_utils as geo_utils
from app.utils.json_utils import parse_llm_json, parse_llm_json_list
from app.utils.translations import translate
from app.utils.vector_store import VectorStore
from app.utils.db_manager import DBManager, Company
from app.models.models import CompanyModel


# ==========================================
# 1. file_utils.py tests
# ==========================================
def test_file_utils_get_file_age_days():
    # Test non-existing file
    assert get_file_age_days("non_existing_file.txt") == 0

    # Test existing file
    with patch("os.path.exists", return_value=True), \
         patch("os.path.getmtime", return_value=time.time() - (3 * 24 * 3600)): # 3 days ago
        assert get_file_age_days("dummy.txt") == 3


# ==========================================
# 2. fit_explorer.py tests
# ==========================================
def test_fit_explorer():
    mock_html = """
    <html>
        <head>
            <script src="/js/test.js"></script>
            <script>console.log("inline");</script>
        </head>
        <body>
            <a href="/login">Anmelden</a>
        </body>
    </html>
    """
    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = mock_html.encode("utf-8")

        # Running this should print to stdout and not crash
        explore_fit()


# ==========================================
# 3. geo_utils.py tests
# ==========================================
@pytest.fixture(autouse=True)
def reset_geo_globals():
    # Reset all caching and state globals in geo_utils before each test
    geo_utils._geo_cache.clear()
    geo_utils._failed_keys.clear()
    geo_utils._nominatim_disabled = False


def test_geo_utils_load_save_cache(tmp_path):
    test_cache_path = str(tmp_path / "geo_cache.json")
    with patch("app.utils.geo_utils.CACHE_FILE", test_cache_path):
        # Initial empty load
        cache = load_cache()
        assert cache == {}

        # Save some data
        new_data = {"Berlin, Germany": [52.52, 13.40]}
        save_cache(new_data)

        # Force load from disk
        geo_utils._geo_cache = {}
        loaded = load_cache()
        assert loaded["Berlin, Germany"] == (52.52, 13.40)


def test_geo_utils_get_coordinates_empty():
    assert get_coordinates("") is None


def test_geo_utils_get_coordinates_from_cache():
    geo_utils._geo_cache["Cologne, Germany"] = (50.93, 6.95)
    res = get_coordinates("Cologne", "Germany")
    assert res == (50.93, 6.95)


def test_geo_utils_get_coordinates_only_from_cache():
    res = get_coordinates("Munich", "Germany", only_from_cache=True)
    assert res is None


def test_geo_utils_get_coordinates_in_failed_keys():
    geo_utils._failed_keys.add("Paris, France")
    res = get_coordinates("Paris", "France")
    assert res is None


def test_geo_utils_get_coordinates_nominatim_success():
    # Mock Nominatim geocoder
    mock_location = MagicMock()
    mock_location.latitude = 52.52
    mock_location.longitude = 13.40

    with patch("app.utils.geo_utils._nominatim.geocode", return_value=mock_location) as mock_geocode:
        res = get_coordinates("Berlin", "Germany")
        assert res == (52.52, 13.40)
        mock_geocode.assert_called_once_with("Berlin, Germany")
        assert "Berlin, Germany" in geo_utils._geo_cache


def test_geo_utils_get_coordinates_nominatim_retry_then_success():
    from geopy.exc import GeocoderTimedOut
    mock_location = MagicMock()
    mock_location.latitude = 52.52
    mock_location.longitude = 13.40

    # First raises TimedOut, second returns location
    with patch("app.utils.geo_utils._nominatim.geocode", side_effect=[GeocoderTimedOut("Timed out"), mock_location]) as mock_geocode:
        with patch("time.sleep"):  # speed up tests
            res = get_coordinates("Berlin", "Germany", retries=1)
            assert res == (52.52, 13.40)
            assert mock_geocode.call_count == 2


def test_geo_utils_get_coordinates_nominatim_rate_limited():
    from geopy.exc import GeocoderServiceError
    # Nominatim returns 429
    with patch("app.utils.geo_utils._nominatim.geocode", side_effect=GeocoderServiceError("Error 429: Too many requests")) as mock_geo, \
         patch("app.utils.geo_utils._photon.geocode") as mock_photon, \
         patch("time.sleep"):

        mock_photon.return_value = MagicMock(latitude=40.0, longitude=10.0)

        res = get_coordinates("Hamburg", "Germany")
        assert res == (40.0, 10.0)
        assert geo_utils._nominatim_disabled is True


def test_geo_utils_get_coordinates_photon_fallback():
    # Nominatim returns None, Photon returns Hamburg location
    mock_photon_loc = MagicMock(latitude=53.55, longitude=9.99)
    with patch("app.utils.geo_utils._nominatim.geocode", return_value=None), \
         patch("app.utils.geo_utils._photon.geocode", return_value=mock_photon_loc), \
         patch("time.sleep"):

        res = get_coordinates("Hamburg", "Germany")
        assert res == (53.55, 9.99)


def test_geo_utils_get_coordinates_all_fail():
    with patch("app.utils.geo_utils._nominatim.geocode", return_value=None), \
         patch("app.utils.geo_utils._photon.geocode", side_effect=Exception("Failed")), \
         patch("time.sleep"):

        res = get_coordinates("Nowhere", "Germany")
        assert res is None
        assert "Nowhere, Germany" in geo_utils._failed_keys


def test_geo_utils_batch_geocode():
    # List of company dicts/objects
    company_obj = MagicMock()
    company_obj.state = "NRW"
    company_obj.city = "Düsseldorf"
    company_obj.country = "Germany"

    company_dict = {
        "State": "nordrhein-westfalen",
        "City": "Köln",
        "Land": "Germany"
    }

    # Non NRW
    company_non_nrw = {
        "State": "Bayern",
        "City": "München"
    }

    mock_loc = MagicMock(latitude=50.0, longitude=5.0)

    with patch("app.utils.geo_utils._nominatim.geocode", return_value=mock_loc), \
         patch("app.utils.geo_utils.save_cache") as mock_save_cache, \
         patch("time.sleep"):

        batch_geocode([company_obj, company_dict, company_non_nrw])

        assert "Düsseldorf, Germany" in geo_utils._geo_cache
        assert "Köln, Germany" in geo_utils._geo_cache
        assert "München, Germany" not in geo_utils._geo_cache
        mock_save_cache.assert_called_once()


# ==========================================
# 4. json_utils.py tests
# ==========================================
def test_json_utils_parse_llm_json():
    # Test None/empty
    assert parse_llm_json("") is None
    assert parse_llm_json(None) is None

    # Test clean JSON
    assert parse_llm_json('{"foo": "bar"}') == {"foo": "bar"}

    # Test markdown JSON block
    markdown_json = "```json\n{\n  \"hello\": \"world\"\n}\n```"
    assert parse_llm_json(markdown_json) == {"hello": "world"}

    # Test extra text around JSON
    wrapped_json = "Here is your JSON response: {\"key\": \"val\"} hope you like it!"
    assert parse_llm_json(wrapped_json) == {"key": "val"}

    # Test totally invalid JSON
    assert parse_llm_json("not json at all") is None


def test_json_utils_parse_llm_json_list():
    # Test None/empty
    assert parse_llm_json_list("") is None

    # Test clean list
    assert parse_llm_json_list("[1, 2, 3]") == [1, 2, 3]

    # Test markdown list block
    markdown_list = "```json\n[\"a\", \"b\"]\n```"
    assert parse_llm_json_list(markdown_list) == ["a", "b"]

    # Test extra text around list
    wrapped_list = "Here is the list: [1.2, 3.4] end."
    assert parse_llm_json_list(wrapped_list) == [1.2, 3.4]

    # Test invalid list
    assert parse_llm_json_list("not list") is None


# ==========================================
# 5. translations.py tests
# ==========================================
def test_translations():
    # Test default/de translation
    assert translate("page_title", "de") == "Förderrecherche App"
    # Test en translation
    assert translate("page_title", "en") == "Funding Research App"
    # Test fallback to de if lang not found
    assert translate("page_title", "fr") == "Förderrecherche App"
    # Test placeholder formatting
    assert translate("age_days", "de", days=5) == "5 Tage alt"
    # Test missing key fallback (returns the key itself)
    assert translate("completely_missing_key", "de") == "completely_missing_key"


# ==========================================
# 6. vector_store.py tests
# ==========================================
def test_vector_store():
    # Mock chroma db PersistentClient
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    with patch("chromadb.PersistentClient", return_value=mock_client) as mock_db_init:
        # Create store
        vs = VectorStore(persist_directory="test_persist")
        mock_db_init.assert_called_once_with(path="test_persist")
        mock_client.get_or_create_collection.assert_called_once_with(name="companies")

        # Test add_company_vector with dict metadata
        vs.add_company_vector("c1", "some text representation", {"name": "C1", "employees_count": 10})
        mock_collection.upsert.assert_called_with(
            documents=["some text representation"],
            metadatas=[{"name": "C1", "employees_count": 10}],
            ids=["c1"]
        )

        # Test add_company_vector with CompanyModel
        model = CompanyModel(name="C2", url="https://c2.com", employees_count=20)
        vs.add_company_vector("c2", "c2 text representation", model)
        mock_collection.upsert.assert_called_with(
            documents=["c2 text representation"],
            metadatas=[model.model_dump()],
            ids=["c2"]
        )

        # Test query_companies
        mock_collection.query.return_value = {"ids": ["c1"], "documents": ["doc1"]}
        res = vs.query_companies("AI research", n_results=3, where={"kmu_status": True})
        mock_collection.query.assert_called_with(
            query_texts=["AI research"],
            n_results=3,
            where={"kmu_status": True},
            where_document=None
        )
        assert res == {"ids": ["c1"], "documents": ["doc1"]}


# ==========================================
# 7. db_manager.py tests
# ==========================================
def test_db_manager():
    # Use SQLite in-memory database
    db = DBManager(db_url="sqlite:///:memory:")

    # Verify is_url_indexed returns False for empty or unindexed url
    assert db.is_url_indexed("") is False
    assert db.is_url_indexed("https://notindexed.com") is False

    # Create dummy companies
    c1 = {
        "name": "Company One",
        "url": "https://company1.com/",
        "employees_count": 10,
        "kmu_status": True,
        "city": "Köln",
        "state": "NRW",
    }
    c2 = {
        "name": "Company Two",
        "url": "https://company2.com",
        "employees_count": "not an int",  # triggers exception handling & default to None
        "kmu_status": False,
        "city": "Düsseldorf",
        "state": "NRW",
    }

    # Add companies
    db.add_company(c1)
    db.add_company(c2)

    # Check they are indexed
    assert db.is_url_indexed("https://company1.com") is True
    assert db.is_url_indexed("https://company1.com/") is True
    assert db.is_url_indexed("https://company2.com") is True

    # Retrieve all
    companies = db.get_all_companies()
    assert len(companies) == 2
    c1_retrieved = next(c for c in companies if c.name == "Company One")
    assert c1_retrieved.url == "https://company1.com"  # stripped trailing slash
    assert c1_retrieved.employees_count == 10

    c2_retrieved = next(c for c in companies if c.name == "Company Two")
    assert c2_retrieved.employees_count is None  # invalid cast default to None

    # Update company
    update_data = [
        {"url": "https://company1.com", "employees_count": 15},
        CompanyModel(name="Updated Two", url="https://company2.com", city="Aachen")
    ]
    db.update_companies(update_data)

    companies_updated = db.get_all_companies()
    c1_up = next(c for c in companies_updated if c.url == "https://company1.com")
    assert c1_up.employees_count == 15
    c2_up = next(c for c in companies_updated if c.url == "https://company2.com")
    assert c2_up.name == "Updated Two"
    assert c2_up.city == "Aachen"

    # Test deduplication
    # Let's insert a duplicate company with raw SQL / bypass to create a true duplicate.
    # "https://company3.com" and "https://company3.com/" are different strings,
    # so they bypass the SQL UNIQUE constraint, but they normalize to the same url.
    session = db.Session()
    session.add(Company(name="Dup One", url="https://company3.com"))
    session.add(Company(name="Dup Two", url="https://company3.com/"))
    session.commit()
    session.close()

    assert len(db.get_all_companies()) == 4

    # Call deduplicate
    removed_count = db.deduplicate_companies()
    assert removed_count == 1
    assert len(db.get_all_companies()) == 3

    # Test add_company update path
    # If we add an existing URL, it should update it
    db.add_company({"url": "https://company1.com", "city": "Bonn"})
    c1_final = next(c for c in db.get_all_companies() if c.url == "https://company1.com")
    assert c1_final.city == "Bonn"

    # Test exception handling inside transactions (simulate failure on query or commit)
    with patch("sqlalchemy.orm.Session.commit", side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            db.add_company({"url": "https://error.com"})

        with pytest.raises(Exception):
            db.update_companies([{"url": "https://company1.com", "city": "Failed"}])

    # insert duplicates so deduplicate actually commits (without mock active)
    session = db.Session()
    session.add(Company(name="Dup Three", url="https://company4.com"))
    session.add(Company(name="Dup Four", url="https://company4.com/"))
    session.commit()
    session.close()

    # Now run deduplicate under mock to make deduplicate commit fail
    with patch("sqlalchemy.orm.Session.commit", side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            db.deduplicate_companies()
