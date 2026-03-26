from unittest.mock import MagicMock, patch
from app.services.indexing_service import IndexingService
from app.utils.db_manager import DBManager
from app.utils.vector_store import VectorStore
from app.services.llm_service import LLMService

def test_indexing_service():
    """
    Verifies that IndexingService can crawl and index company data.
    """
    # Arrange
    mock_llm_service = MagicMock(spec=LLMService)
    mock_db_manager = MagicMock(spec=DBManager)
    mock_vector_store = MagicMock(spec=VectorStore)

    # Mock LLM response
    mock_llm_service.extract_structured_data.return_value = '{"Name": "Test Company", "Bundesland": "NRW", "Zusammenfassung": "A test company summary."}'

    with patch("app.services.scraper_service.ScraperService.fetch_page_content") as mock_fetch:
        mock_fetch.return_value = {
            "text": "This is a test company website content.",
            "final_url": "https://testcompany.com"
        }

        indexing_service = IndexingService(mock_llm_service, mock_db_manager, mock_vector_store)
        links = ["https://testcompany.com"]

        # Act
        indexing_service.index_companies_from_links(links)

        # Assert
        mock_fetch.assert_called_once_with("https://testcompany.com")
        mock_db_manager.add_company.assert_called_once()
        mock_vector_store.add_company_vector.assert_called_once()
        print("IndexingService test passed.")

if __name__ == "__main__":
    test_indexing_service()
