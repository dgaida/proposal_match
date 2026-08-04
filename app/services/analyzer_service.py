from collections.abc import Callable

from app.models.models import ResearchCallModel
from app.services.llm_service import LLMService
from app.utils.json_utils import parse_llm_json


class AnalyzerService:
    """
    Service for analyzing research call text and extracting structured metadata.

    Attributes:
        llm_service (LLMService): The LLM service used for extraction.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the AnalyzerService.

        Args:
            llm_service (LLMService): The LLM service to use.
        """
        self.llm_service = llm_service

    def analyze_research_call(
        self,
        text: str,
        url: str | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> ResearchCallModel | None:
        """
        Analyzes a research call using LLM to extract key details.

        Args:
            text (str): The text content of the research call.
            url (Optional[str]): The source URL of the call.
            status_callback (Optional[Callable[[str], None]]): Callback for status updates.

        Returns:
            Optional[ResearchCallModel]: A validated model with extracted call details or None if extraction fails.

        Raises:
            Exception: Propagates exceptions from the LLM service.
        """
        prompt = f"""
        Analyze the research call {f"from the URL {url}" if url else ""} and extract the following information in JSON format:
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
        - Link: The URL to the research call. {f"Use {url}" if url else "Extract from text if available."}
        - Beschreibung: A detailed textual description of the call in German, including the most important contents, research goals, etc., formatted in Markdown.
          Important: The description MUST include a separate paragraph for 'Forschungsschwerpunkte' (or 'Gegenstand der Förderung').
          The total length of the 'Beschreibung' text should be at least 800 tokens.

        Return only the JSON object.
        """
        try:
            response = self.llm_service.extract_structured_data(
                text, prompt, status_callback=status_callback
            )

            # Use the utility to extract JSON from the response
            json_response = parse_llm_json(response)
            if json_response:
                try:
                    return ResearchCallModel.model_validate(json_response)
                except Exception as e:
                    print(f"Failed to validate ResearchCallModel: {e}")
                    return None

            return None
        except Exception:
            # Re-raise to let the caller handle the specific exception (useful for UI error messages)
            raise
