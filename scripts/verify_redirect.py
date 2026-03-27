from app.services.scraper_service import ScraperService

scraper = ScraperService()
# This URL is known to redirect
url = "https://www.innovationlab.de/en/"
result = scraper.fetch_page_content(url)

if result:
    print(f"Final URL: {result['final_url']}")
    print(f"Text length: {len(result['text'])}")
    assert result['final_url'].rstrip('/') == "https://innovationlab.de"
    print("Redirect verification successful!")
else:
    print("Failed to fetch content.")
