from unittest.mock import MagicMock, patch
from app.services.matching_service import MatchingService
from app.utils.db_manager import Company
from app.utils.vector_store import VectorStore
from app.services.llm_service import LLMService


def test_matching_service_hybrid_search():
    """
    Verifies that MatchingService can perform hybrid search using ChromaDB and SQLite.
    """
    # Arrange
    mock_llm_service = MagicMock(spec=LLMService)
    # Don't use spec=DBManager to avoid strict attribute checks on MagicMock
    mock_db_manager = MagicMock()
    mock_vector_store = MagicMock(spec=VectorStore)

    # Mock ChromaDB response
    mock_vector_store.query_companies.return_value = {
        "ids": [["https://test1.com", "https://test2.com"]]
    }

    # Mock SQLite response
    mock_company1 = Company(
        name="Test Company 1", url="https://test1.com", state="NRW", industry="AI"
    )
    mock_company2 = Company(
        name="Test Company 2",
        url="https://test2.com",
        state="Bavaria",
        industry="Cloud",
    )

    mock_session = MagicMock()
    mock_db_manager.Session.return_value = mock_session
    mock_query_obj = mock_session.query.return_value
    mock_query_obj.filter.return_value = mock_query_obj
    mock_query_obj.all.return_value = [mock_company1, mock_company2]

    matching_service = MatchingService(
        mock_llm_service, mock_db_manager, mock_vector_store
    )
    query = "AI Companies"

    # Act
    results = matching_service.hybrid_search(query)

    # Assert
    assert len(results) == 2
    assert results[0].name == "Test Company 1"
    assert results[1].name == "Test Company 2"
    print("MatchingService hybrid search test passed.")


def test_matching_service_internet_search():
    """
    Verifies that MatchingService can search the internet for companies.
    """
    with patch("app.services.matching_service.DDGS") as MockDDGS:
        # Arrange
        mock_ddgs_instance = MockDDGS.return_value.__enter__.return_value
        mock_ddgs_instance.text.return_value = [
            {
                "title": "Internet Co",
                "href": "https://internet.com",
                "body": "Web snippet",
            }
        ]

        matching_service = MatchingService(MagicMock(), MagicMock(), MagicMock())
        topic = "Sustainable Energy"

        # Act
        results = matching_service.search_internet_for_companies(topic)

        # Assert
        assert len(results) == 1
        assert results[0]["name"] == "Internet Co"
        assert results[0]["url"] == "https://internet.com"
        print("MatchingService internet search test passed.")


if __name__ == "__main__":
    test_matching_service_hybrid_search()
    test_matching_service_internet_search()
