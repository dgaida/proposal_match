from unittest.mock import patch
from app.services.scraper_service import ScraperService
from app.services.analyzer_service import AnalyzerService


def test_scraper_service():
    """
    Verifies that ScraperService can fetch content from a URL.
    """
    with patch("httpx.Client.get") as mock_get:
        # Arrange
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = (
            b"<html><body><h1>Test Title</h1><p>Test Content</p></body></html>"
        )

        scraper_service = ScraperService()
        url = "https://example.com/research-call"

        # Act
        result = scraper_service.fetch_page_content(url)

        # Assert
        assert result is not None
        assert "Test Title" in result["text"]
        assert "Test Content" in result["text"]
        print("ScraperService test passed.")


def test_analyzer_service():
    """
    Verifies that AnalyzerService can extract structured data using the LLM.
    """
    with patch("app.services.llm_service.LLMService") as MockLLMService:
        # Arrange
        mock_llm_service_instance = MockLLMService.return_value
        mock_llm_service_instance.extract_structured_data.return_value = (
            '{"Thema": "AI in Healthcare", "Deadline": "2026-12-31"}'
        )

        analyzer_service = AnalyzerService(mock_llm_service_instance)
        text = "AI in Healthcare. Deadline: 2026-12-31"

        # Act
        result = analyzer_service.analyze_research_call(text)

        # Assert
        assert result is not None
        assert result.thema == "AI in Healthcare"
        assert result.deadline == "2026-12-31"
        print("AnalyzerService test passed.")


if __name__ == "__main__":
    test_scraper_service()
    test_analyzer_service()
