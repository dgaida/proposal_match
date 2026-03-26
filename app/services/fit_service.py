import httpx
import json
from typing import List, Dict, Any
from app.services.llm_service import LLMService

class FITService:
    def __init__(self, llm_service: LLMService, base_url: str = "https://fit.uni-kassel.de/api"):
        self.base_url = base_url
        self.llm_service = llm_service
        self.auth_url = "https://fit.uni-kassel.de/auth"
        self.client = httpx.Client(timeout=30)

    def login(self, username: str, password: str) -> bool:
        """
        Authenticates with Keycloak to get a bearer token.
        """
        data = {
            "grant_type": "password",
            "client_id": "web",
            "username": username,
            "password": password,
            "scope": "openid"
        }
        try:
            token_url = f"{self.auth_url}/realms/FIT/protocol/openid-connect/token"
            response = self.client.post(token_url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.client.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
                return True
            else:
                print(f"Login failed: {response.status_code} {response.text}")
                return False
        except Exception as e:
            print(f"Error during login: {e}")
            return False

    def search_calls(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches for calls in the FIT database and filters for relevance using LLM.
        """
        params = {
            "search": query,
            "pageSize": 20, # Fetch more to allow for filtering
            "sortBy": "updatedAt",
            "descending": "true"
        }
        try:
            response = self.client.get(f"{self.base_url}/articles", params=params)
            response.raise_for_status()
            data = response.json()
            docs = data.get("docs", [])

            if not docs:
                return []

            # Post-filtering using LLM for relevance
            return self._filter_relevant_calls(docs, query)
        except Exception as e:
            print(f"Error searching FIT: {e}")
            return []

    def _filter_relevant_calls(self, docs: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Uses the LLM to filter and rank the fetched calls based on the original query.
        """
        # Prepare data for LLM
        simplified_docs = []
        for i, d in enumerate(docs):
            simplified_docs.append({
                "id": i,
                "title": d.get('title') or d.get('englishTitle'),
                "description": d.get('shortDescription') or d.get('description')
            })

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
            {"role": "system", "content": "You are an expert at filtering research funding opportunities for relevance."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.llm_service.chat_completion(messages)
            # Basic cleanup in case of extra text
            start_index = response.find("[")
            end_index = response.rfind("]") + 1
            if start_index != -1 and end_index != -1:
                relevant_ids = json.loads(response[start_index:end_index])
                return [docs[i] for i in relevant_ids if i < len(docs)]
            return docs[:10] # Fallback to first 10 if parsing fails
        except Exception as e:
            print(f"Error filtering FIT calls: {e}")
            return docs[:10]

    def summarize_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Summarizes the search results using the LLM.
        """
        if not results:
            return "No relevant results found."

        formatted_results = "\n\n".join([
            f"Title: {r.get('title') or r.get('englishTitle')}\nDescription: {r.get('shortDescription') or r.get('description')}"
            for r in results
        ])

        prompt = f"""
        Below are search results from a research funding database.
        Summarize the most relevant calls for the user's interest.
        Highlight key data like topic, deadline, and eligibility.

        Results:
        {formatted_results}
        """

        messages = [
            {"role": "system", "content": "You are an assistant summarizing research funding opportunities."},
            {"role": "user", "content": prompt}
        ]

        return self.llm_service.chat_completion(messages)
