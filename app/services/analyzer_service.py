import json
from typing import Dict, Any, Optional
from app.services.llm_service import LLMService

class AnalyzerService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def analyze_research_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyzes the research call text and extracts key information using the LLM.
        """
        prompt = """
        Analyze the research call and extract the following information in JSON format:
        - Thema: The research topic.
        - Zielsetzung: The primary goal or objective.
        - Deadline: The application deadline.
        - Einstufig_Zweistufig: Is it a 1-step or 2-step process?
        - Anzahl_Projektpartner: Required or suggested number of project partners.
        - Budget: Estimated or maximum budget for the call.
        - Laufzeit: The duration of the projects.
        - Andere_Metadaten: Any other relevant information.

        Return only the JSON object.
        """
        try:
            response = self.llm_service.extract_structured_data(text, prompt)

            # Use the LLM to process and format the response as JSON
            # This is to handle potential cases where the response is not perfectly formatted JSON
            json_response = self._parse_json(response)

            return json_response
        except Exception as e:
            print(f"Error analyzing research call: {e}")
            return None

    def _parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Attempts to parse the response from the LLM as a JSON object.
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
