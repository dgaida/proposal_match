import json
import os
import re
from typing import List, Dict, Any, Optional, Callable
from app.services.scraper_service import ScraperService
from app.services.llm_service import LLMService
from app.utils.db_manager import DBManager
from app.utils.vector_store import VectorStore

class IndexingService:
    def __init__(self, llm_service: LLMService, db_manager: DBManager, vector_store: VectorStore):
        self.llm_service = llm_service
        self.db_manager = db_manager
        self.vector_store = vector_store
        self.scraper_service = ScraperService()

    def index_companies_from_links(self, links: List[str]) -> int:
        """
        Crawls the given links, extracts information, and stores it.
        Returns the number of companies actually indexed.
        """
        indexed_count = 0
        for link in links:
            # Normalize URL: change http:// to https://
            if link.startswith("http://"):
                link = link.replace("http://", "https://", 1)

            scraper_result = self.scraper_service.fetch_page_content(link)
            if scraper_result:
                content = scraper_result["text"]
                final_url = scraper_result["final_url"]

                # Check if final URL is already indexed
                if self.db_manager.is_url_indexed(final_url):
                    continue

                extracted_data = self._extract_company_info(content, final_url)
                if extracted_data:
                    # Split metadata and semantic info for storage
                    summary = extracted_data.get("Zusammenfassung")
                    if isinstance(summary, list):
                        summary = "\n".join(str(s) for s in summary)

                    products = extracted_data.get("Produkte")
                    if isinstance(products, list):
                        products = "\n".join(str(p) for p in products)

                    metadata = {
                        "name": extracted_data.get("Name"),
                        "url": final_url,
                        "state": extracted_data.get("Bundesland"),
                        "city": extracted_data.get("Stadt"),
                        "country": extracted_data.get("Land"),
                        "org_type": extracted_data.get("Organisationsart"),
                        "employees_count": extracted_data.get("Anzahl_Mitarbeiter"),
                        "kmu_status": extracted_data.get("KMU_Status"),
                        "industry": extracted_data.get("Branche"),
                        "research_active": extracted_data.get("Bereits_aktiv_in_Forschungsprojekten"),
                        "summary": summary,
                        "products": products
                    }

                    # Store in SQLite
                    self.db_manager.add_company(metadata)

                    # Store in ChromaDB
                    semantic_text = f"Company: {metadata['name']}. {metadata['summary']} Products: {metadata['products']}"
                    self.vector_store.add_company_vector(final_url, semantic_text, metadata)
                    indexed_count += 1
        return indexed_count

    def _extract_company_info(self, text: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Extracts company information from the given text using the LLM.
        """
        prompt = f"""
        Extract the following information from the text for the organization website {url} in JSON format:
        - Name: The name of the organization.
        - Land: The country of the organization.
        - Bundesland: The state (German "Bundesland"), if applicable.
        - Stadt: The city.
        - Organisationsart: The type of organization (e.g., "Unternehmen", "Forschungseinrichtung", "Hochschule", "Kommunen").
        - Anzahl_Mitarbeiter: Approximate number of employees (null for non-companies).
        - KMU_Status: Is it an SME? (Boolean, null for non-companies).
        - Branche: Industry/Sector.
        - Bereits_aktiv_in_Forschungsprojekten: Has the organization been active in research projects? (Boolean).
        - Zusammenfassung: A brief summary of the organization. MUST BE IN GERMAN.
        - Produkte: Description of important products or services.

        Return only the JSON object.
        """
        try:
            response = self.llm_service.extract_structured_data(text, prompt)
            return self._parse_json(response)
        except Exception as e:
            print(f"Error extracting company info: {e}")
            return None

    def index_from_folder(self, folder_path: str, limit: int = 25, status_callback: Optional[Callable[[str], None]] = None) -> List[str]:
        """
        Recursively searches for .url files in the folder and indexes the URLs.
        """
        indexed_urls = []
        if not os.path.exists(folder_path):
            return indexed_urls

        # Get all existing URLs in the database to avoid re-indexing
        existing_urls = {c.url.rstrip('/') for c in self.db_manager.get_all_companies()}
        processed_in_this_run = set()

        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".url"):
                    file_path = os.path.join(root, file)
                    url = self._extract_url_from_file(file_path)
                    if url:
                        normalized_url = url.rstrip('/')
                        if normalized_url in existing_urls or normalized_url in processed_in_this_run:
                            if status_callback:
                                status_callback(f"Skipping already indexed or duplicate URL: {url}")
                            continue

                        if status_callback:
                            status_callback(f"Indexing company: {url} (found in {file})")

                        newly_indexed = self.index_companies_from_links([url])
                        if newly_indexed > 0:
                            indexed_urls.append(url)
                        processed_in_this_run.add(url)

                if len(indexed_urls) >= limit:
                    return indexed_urls
        return indexed_urls

    def _extract_url_from_file(self, file_path: str) -> Optional[str]:
        """
        Extracts the URL from a .url file.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # .url files typically have a line "URL=..."
                match = re.search(r"URL=(.+)", content)
                if match:
                    return match.group(1).strip()
        except Exception as e:
            print(f"Error reading .url file {file_path}: {e}")
        return None

    def _parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Attempts to parse the response from the LLM as a JSON object.
        """
        try:
            start_index = response.find("{")
            end_index = response.rfind("}") + 1
            if start_index != -1 and end_index != -1:
                json_data = response[start_index:end_index]
                return json.loads(json_data)
            return json.loads(response)
        except (ValueError, json.JSONDecodeError):
            return None
