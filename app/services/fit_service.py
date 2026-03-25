import httpx
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
        Note: Implementing full Keycloak flow with direct grant for simulation.
        Real implementation would need the correct realm and client_id discovered in investigation.
        """
        # Keycloak Direct Grant Flow (Resource Owner Password Credentials)
        # Assuming the realm is 'FIT' and client_id is 'web' as found
        data = {
            "grant_type": "password",
            "client_id": "web",
            "username": username,
            "password": password,
            "scope": "openid"
        }
        try:
            # The token endpoint is usually at /realms/{realm}/protocol/openid-connect/token
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
        Searches for calls in the FIT database.
        Endpoint: /api/articles
        """
        params = {
            "search": query,
            "pageSize": 10,
            "sortBy": "updatedAt",
            "descending": "true"
        }
        try:
            response = self.client.get(f"{self.base_url}/articles", params=params)
            response.raise_for_status()
            data = response.json()
            # The API returns an object with 'docs' containing the articles
            return data.get("docs", [])
        except Exception as e:
            print(f"Error searching FIT: {e}")
            return []

    def summarize_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Summarizes the search results using the LLM.
        """
        if not results:
            return "No results found."

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
