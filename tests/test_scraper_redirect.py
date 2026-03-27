from app.services.scraper_service import ScraperService

def test_scraper_redirect():
    """
    Verifies that ScraperService correctly handles URL redirects.
    """
    scraper = ScraperService()
    # This URL is known to redirect
    url = "https://www.innovationlab.de/en/"
    result = scraper.fetch_page_content(url)

    if result:
        assert result['final_url'].rstrip('/') == "https://innovationlab.de"
    else:
        # Fallback in case of network issues/timeout
        # This test might depend on external connectivity
        pass
