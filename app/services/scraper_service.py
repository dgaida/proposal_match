import httpx
from bs4 import BeautifulSoup
from typing import Optional


class ScraperService:
    """Service for scraping and cleaning web content.

    Attributes:
        timeout (int): The HTTP request timeout in seconds.
    """

    def __init__(self, timeout: int = 30):
        """Initializes the ScraperService with a timeout.

        Args:
            timeout (int): The HTTP request timeout in seconds.
        """
        self.timeout = timeout

    def fetch_page_content(self, url: str) -> Optional[dict]:
        """Fetches the text content of a given URL and follows redirects.

        Args:
            url (str): The URL to fetch content from.

        Returns:
            Optional[dict]: A dictionary containing 'text' and 'final_url', or None on failure.
        """
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                final_url = str(response.url)
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract text from relevant tags
                for script in soup(["script", "style"]):
                    script.extract()  # Remove scripts and styles

                text = soup.get_text(separator="\n")

                # Basic cleaning
                lines = (line.strip() for line in text.splitlines())
                chunks = (
                    phrase.strip() for line in lines for phrase in line.split("  ")
                )
                text = "\n".join(chunk for chunk in chunks if chunk)

                return {"text": text, "final_url": final_url}
        except Exception as e:
            print(f"Error fetching page content: {e}")
            return None
