import json
from typing import List, Dict, Any, Optional
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

    def index_companies_from_links(self, links: List[str]):
        """
        Crawls the given links, extracts information, and stores it.
        """
        for link in links:
            content = self.scraper_service.fetch_page_content(link)
            if content:
                extracted_data = self._extract_company_info(content, link)
                if extracted_data:
                    # Split metadata and semantic info for storage
                    metadata = {
                        "name": extracted_data.get("Name"),
                        "url": link,
                        "state": extracted_data.get("Bundesland"),
                        "city": extracted_data.get("Stadt"),
                        "employees_count": extracted_data.get("Anzahl_Mitarbeiter"),
                        "kmu_status": extracted_data.get("KMU_Status"),
                        "industry": extracted_data.get("Branche"),
                        "research_active": extracted_data.get("Bereits_aktiv_in_Forschungsprojekten"),
                        "summary": extracted_data.get("Zusammenfassung"),
                        "products": extracted_data.get("Produkte")
                    }

                    # Store in SQLite
                    self.db_manager.add_company(metadata)

                    # Store in ChromaDB
                    semantic_text = f"Company: {metadata['name']}. {metadata['summary']} Products: {metadata['products']}"
                    self.vector_store.add_company_vector(link, semantic_text, metadata)

    def _extract_company_info(self, text: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Extracts company information from the given text using the LLM.
        """
        prompt = f"""
        Extract the following information from the text for the company website {url} in JSON format:
        - Name: The name of the company.
        - Bundesland: The state (German "Bundesland").
        - Stadt: The city.
        - Anzahl_Mitarbeiter: Approximate number of employees.
        - KMU_Status: Is it an SME? (Boolean).
        - Branche: Industry/Sector.
        - Bereits_aktiv_in_Forschungsprojekten: Has the company been active in research projects? (Boolean).
        - Zusammenfassung: A brief summary of the company.
        - Produkte: Description of important products.

        Return only the JSON object.
        """
        try:
            response = self.llm_service.extract_structured_data(text, prompt)
            return self._parse_json(response)
        except Exception as e:
            print(f"Error extracting company info: {e}")
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
