import json
from typing import Dict, Any, Optional


def parse_llm_json(response: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to parse an LLM response string into a dictionary.

    Handles potential extra text before or after the JSON block.

    Args:
        response (str): The raw string response from the LLM.

    Returns:
        Optional[Dict[str, Any]]: The parsed dictionary or None if parsing fails.
    """
    if not response:
        return None

    # Basic cleanup in case of extra text or markdown blocks
    clean_response = response.strip()
    if clean_response.startswith("```json"):
        clean_response = clean_response[7:]
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3]

    try:
        # First attempt: directly parse the entire response
        return json.loads(clean_response)
    except (ValueError, json.JSONDecodeError):
        # Second attempt: extract the first JSON object from the response
        try:
            start_index = clean_response.find("{")
            end_index = clean_response.rfind("}") + 1
            if start_index != -1 and end_index != -1:
                json_data = clean_response[start_index:end_index]
                return json.loads(json_data)
        except (ValueError, json.JSONDecodeError):
            pass

    return None


def parse_llm_json_list(response: str) -> Optional[list]:
    """
    Attempts to parse an LLM response string into a list.

    Handles potential extra text or markdown blocks.

    Args:
        response (str): The raw string response from the LLM.

    Returns:
        Optional[list]: The parsed list or None if parsing fails.
    """
    if not response:
        return None

    # Basic cleanup in case of extra text or markdown blocks
    clean_response = response.strip()
    if clean_response.startswith("```json"):
        clean_response = clean_response[7:]
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3]

    try:
        # First attempt: directly parse the entire response
        return json.loads(clean_response)
    except (ValueError, json.JSONDecodeError):
        # Second attempt: extract the first JSON list from the response
        try:
            start_index = clean_response.find("[")
            end_index = clean_response.rfind("]") + 1
            if start_index != -1 and end_index != -1:
                json_data = clean_response[start_index:end_index]
                return json.loads(json_data)
        except (ValueError, json.JSONDecodeError):
            pass

    return None
