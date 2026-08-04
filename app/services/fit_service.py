import json
from collections.abc import Callable
from typing import Any

import httpx

from app.services.llm_service import LLMService
from app.utils.json_utils import parse_llm_json_list


class FITService:
    """
    Service for interacting with the FIT Uni Kassel research funding database.

    Attributes:
        base_url (str): The base URL for the FIT API.
        llm_service (LLMService): The LLM service for filtering and summarizing.
        auth_url (str): The URL for Keycloak authentication.
        client (httpx.Client): The HTTP client for making API requests.
    """

    def __init__(
        self, llm_service: LLMService, base_url: str = "https://fit.uni-kassel.de/api"
    ):
        """
        Initializes the FITService.

        Args:
            llm_service (LLMService): The LLM service for analysis.
            base_url (str): The API base URL.
        """
        self.base_url = base_url
        self.llm_service = llm_service
        self.auth_url = "https://fit.uni-kassel.de/auth"
        self.client = httpx.Client(timeout=30)

    def login(
        self,
        username: str,
        password: str,
        status_callback: Callable[[str], None] | None = None,
    ) -> bool:
        """
        Authenticates with Keycloak to obtain an access token.

        Args:
            username (str): The FIT username.
            password (str): The FIT password.
            status_callback (Optional[Callable[[str], None]]): Callback for status updates.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        if status_callback:
            status_callback("Logging in to FIT Uni Kassel...")
        data = {
            "grant_type": "password",
            "client_id": "web",
            "username": username,
            "password": password,
            "scope": "openid",
        }
        try:
            token_url = f"{self.auth_url}/realms/FIT/protocol/openid-connect/token"
            response = self.client.post(token_url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.client.headers.update(
                    {"Authorization": f"Bearer {token_data['access_token']}"}
                )
                return True
            else:
                print(f"Login failed: {response.status_code} {response.text}")
                return False
        except Exception as e:
            print(f"Error during login: {e}")
            return False

    def search_calls(
        self, query: str, status_callback: Callable[[str], None] | None = None
    ) -> list[dict[str, Any]]:
        """
        Searches for research calls on FIT and uses LLM for relevance filtering.

        Args:
            query (str): The search query.
            status_callback (Optional[Callable[[str], None]]): Callback for status updates.

        Returns:
            List[Dict[str, Any]]: A list of relevant research call documents.
        """
        if status_callback:
            status_callback(f"Searching for '{query}' on FIT...")
        params = {
            "search": query,
            "pageSize": 20,  # Fetch more to allow for filtering
            "sortBy": "updatedAt",
            "descending": "true",
        }
        try:
            response = self.client.get(f"{self.base_url}/articles", params=params)
            response.raise_for_status()
            data = response.json()
            docs = data.get("docs", [])

            if not docs:
                return []

            # Post-filtering using LLM for relevance
            if status_callback:
                status_callback(f"Filtering {len(docs)} results for relevance...")
            return self._filter_relevant_calls(docs, query)
        except Exception as e:
            print(f"Error searching FIT: {e}")
            return []

    def _filter_relevant_calls(
        self, docs: list[dict[str, Any]], query: str
    ) -> list[dict[str, Any]]:
        """
        Filters a list of documents for relevance to a query using an LLM.

        Args:
            docs (List[Dict[str, Any]]): The list of documents to filter.
            query (str): The original search query.

        Returns:
            List[Dict[str, Any]]: The filtered and ranked list of relevant documents.
        """
        # Prepare data for LLM
        simplified_docs = []
        for i, d in enumerate(docs):
            simplified_docs.append(
                {
                    "id": i,
                    "title": d.get("title") or d.get("englishTitle"),
                    "description": d.get("shortDescription") or d.get("description"),
                }
            )

        prompt = f"""
        Below is a list of research funding calls fetched from a database for the query: "{query}".
        Identify which of these calls are truly relevant to the query.
        Rank them by relevance and return only the IDs of the relevant calls as a JSON list of integers.
        If none are relevant, return an empty list.

        Calls:
        {json.dumps(simplified_docs)}

        Return format: [0, 2, 5]
        """

        messages = [
            {
                "role": "system",
                "content": "You are an expert at filtering research funding opportunities for relevance.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.llm_service.chat_completion(messages)
            relevant_ids = parse_llm_json_list(response)
            if relevant_ids is not None:
                return [
                    docs[i]
                    for i in relevant_ids
                    if isinstance(i, int) and i < len(docs)
                ]
            return docs[:10]  # Fallback to first 10 if parsing fails
        except Exception as e:
            print(f"Error filtering FIT calls: {e}")
            return docs[:10]

    def summarize_results(
        self,
        results: list[dict[str, Any]],
        status_callback: Callable[[str], None] | None = None,
    ) -> str:
        """
        Generates a summary of research funding results using an LLM.

        Args:
            results (List[Dict[str, Any]]): The search results to summarize.
            status_callback (Optional[Callable[[str], None]]): Callback for status updates.

        Returns:
            str: A formatted summary of the results in German.
        """
        if status_callback:
            status_callback("Summarizing results in German...")

        if not results:
            return "Keine relevanten Ergebnisse gefunden."

        formatted_results = "\n\n".join(
            [
                f"Title: {r.get('title') or r.get('englishTitle')}\nDescription: {r.get('shortDescription') or r.get('description')}"
                for r in results
            ]
        )

        prompt = f"""
        Below are search results from a research funding database.
        Summarize the most relevant calls for the user's interest in GERMAN.
        Highlight key data like topic, deadline, and eligibility.
        The summary must be in German.

        Results:
        {formatted_results}
        """

        messages = [
            {
                "role": "system",
                "content": "You are an assistant summarizing research funding opportunities.",
            },
            {"role": "user", "content": prompt},
        ]

        return self.llm_service.chat_completion(messages)
