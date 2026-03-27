import json
from typing import Dict, Any, Optional, Callable
from app.services.llm_service import LLMService

class AnalyzerService:
    """Service for analyzing research call text and extracting structured metadata.

    Attributes:
        llm_service (LLMService): The LLM service used for extraction.
    """

    def __init__(self, llm_service: LLMService):
        """Initializes the AnalyzerService.

        Args:
            llm_service (LLMService): The LLM service to use.
        """
        self.llm_service = llm_service

    def analyze_research_call(self, text: str, url: Optional[str] = None, status_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        """Analyzes a research call using LLM to extract key details.

        Args:
            text (str): The text content of the research call.
            url (Optional[str]): The source URL of the call.
            status_callback (Optional[Callable[[str], None]]): Callback for status updates.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with extracted call details or None if extraction fails.

        Raises:
            Exception: Propagates exceptions from the LLM service.
        """
        prompt = f"""
        Analyze the research call {f'from the URL {url}' if url else ''} and extract the following information in JSON format:
        - Thema: The research topic.
        - Zielsetzung: The primary goal or objective.
        - Deadline: The application deadline.
        - Sitz_der_Organisation: The location/seat of the organization or the call issuer (e.g., "Deutschland", "Europa", "International").
        - Einstufig_Zweistufig: Is it a 1-step or 2-step process?
        - Anzahl_Projektpartner: Required or suggested number of project partners.
        - Budget: Estimated or maximum budget for the call.
        - Laufzeit: The duration of the projects.
        - Antragsberechtigt: Who is eligible to apply? (e.g., Hochschulen, Unternehmen, KMUs, große Unternehmen, Forschungseinrichtungen, Kommunen, Verbände).
        - Antragsberechtigt_Details: Detailed information on eligibility, specifically mentioning if only SMEs (KMU) are allowed or if there are limits regarding the number of employees, turnover, profit, etc.
        - Andere_Metadaten: Any other relevant information.
        - Link: The URL to the research call. {f'Use {url}' if url else 'Extract from text if available.'}
        - Beschreibung: A detailed textual description of the call in German, including the most important contents, research goals, etc., formatted in Markdown.
          Important: The description MUST include a separate paragraph for 'Forschungsschwerpunkte' (or 'Gegenstand der Förderung').
          The total length of the 'Beschreibung' text should be at least 800 tokens.

        Return only the JSON object.
        """
        try:
            response = self.llm_service.extract_structured_data(text, prompt, status_callback=status_callback)

            # Use the LLM to process and format the response as JSON
            # This is to handle potential cases where the response is not perfectly formatted JSON
            json_response = self._parse_json(response)

            return json_response
        except Exception as e:
            # Re-raise to let the caller handle the specific exception (useful for UI error messages)
            raise e

    def _parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Attempts to parse an LLM response as JSON.

        Args:
            response (str): The raw text response from the LLM.

        Returns:
            Optional[Dict[str, Any]]: The parsed JSON data or None if parsing fails.
        """
        try:
            # Basic cleanup in case of extra text
            start_index = response.find("{")
            end_index = response.rfind("}") + 1
            if start_index != -1 and end_index != -1:
                json_data = response[start_index:end_index]
                return json.loads(json_data)
            return json.loads(response)
        except (ValueError, json.JSONDecodeError):
            print(f"Failed to parse JSON response: {response}")
            return None
