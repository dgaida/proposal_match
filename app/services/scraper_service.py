import httpx
from bs4 import BeautifulSoup
from typing import Optional

class ScraperService:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetches the content of a given URL and returns the text.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract text from relevant tags
                for script in soup(["script", "style"]):
                    script.extract()  # Remove scripts and styles

                text = soup.get_text(separator="\n")

                # Basic cleaning
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = "\n".join(chunk for chunk in chunks if chunk)

                return text
        except Exception as e:
            print(f"Error fetching page content: {e}")
            return None
