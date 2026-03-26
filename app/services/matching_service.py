import json
from typing import List, Dict, Any, Optional
from ddgs import DDGS
from app.services.llm_service import LLMService
from app.utils.db_manager import DBManager, Company
from app.utils.vector_store import VectorStore

class MatchingService:
    def __init__(self, llm_service: LLMService, db_manager: DBManager, vector_store: VectorStore):
        self.llm_service = llm_service
        self.db_manager = db_manager
        self.vector_store = vector_store

    def suggest_research_topics(self, call_data: Dict[str, Any]) -> List[str]:
        """
        Suggests potential research topics based on the call data.
        """
        prompt = f"""
        Given the following research call information, suggest 5 concrete research topics or project ideas.
        Call Data: {json.dumps(call_data)}

        Return the topics as a list.
        """
        messages = [
            {"role": "system", "content": "You are an expert in research and development strategy."},
            {"role": "user", "content": prompt}
        ]
        response = self.llm_service.chat_completion(messages)
        # Simplified parsing for the suggestion list
        return [line.strip("- ").strip("12345. ") for line in response.splitlines() if line.strip()]

    def hybrid_search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Performs a hybrid search combining semantic similarity (ChromaDB) and metadata filters (SQLite).
        """
        # Step 1: Semantic search in ChromaDB
        vector_results = self.vector_store.query_companies(query_text=query, n_results=10)

        # Extract the results from the vector store response
        company_ids = vector_results.get("ids", [[]])[0]

        # Step 2: Fetch full metadata from SQLite and apply filters
        session = self.db_manager.Session()
        query_obj = session.query(Company).filter(Company.url.in_(company_ids))

        if filters:
            if filters.get("state"):
                query_obj = query_obj.filter(Company.state == filters["state"])
            if filters.get("industry"):
                query_obj = query_obj.filter(Company.industry == filters["industry"])
            if filters.get("kmu_status") is not None:
                query_obj = query_obj.filter(Company.kmu_status == filters["kmu_status"])

        results = query_obj.all()
        # Convert to dictionary for easy consumption
        formatted_results = []
        for r in results:
            formatted_results.append({
                "name": r.name,
                "url": r.url,
                "state": r.state,
                "city": r.city,
                "industry": r.industry,
                "summary": r.summary,
                "kmu_status": r.kmu_status
            })

        session.close()
        return formatted_results

    def search_internet_for_companies(self, topic: str) -> List[Dict[str, str]]:
        """
        Searches the internet for companies matching the given topic.
        Uses the LLM to generate optimized search queries.
        """
        # Step 1: Generate optimized search queries using LLM
        query_prompt = f"""
        Generate 3 diverse and highly specific search queries in German and English to find official company websites related to the following topic: "{topic}".
        The goal is to find actual company homepages, not news articles or lists.
        Focus on German companies if the topic implies a German context.

        Example for "AI in machinery":
        1. "Maschinenbau Unternehmen Künstliche Intelligenz Webseite"
        2. "AI solutions for mechanical engineering companies Germany official site"
        3. "Innovative Firmen KI Automatisierung Maschinenbau"

        Return only the 3 queries, one per line.
        """
        messages = [
            {"role": "system", "content": "You are an expert at information retrieval and search engine optimization."},
            {"role": "user", "content": query_prompt}
        ]

        try:
            llm_response = self.llm_service.chat_completion(messages)
            queries = [q.strip("- ").strip("123. ") for q in llm_response.splitlines() if q.strip()]
            # Ensure we have at least the original topic if LLM fails
            if not queries:
                queries = [topic]
        except Exception as e:
            print(f"Error generating search queries: {e}")
            queries = [topic]

        # Step 2: Execute searches and collect results
        companies = {} # Use dict to deduplicate by URL
        with DDGS() as ddgs:
            for query in queries:
                try:
                    # We add "site:.de OR site:.com" or similar intent implicitly via LLM queries
                    results = ddgs.text(query, max_results=5)
                    for r in results:
                        url = r.get("href")
                        if url and url not in companies:
                            companies[url] = {
                                "name": r.get("title"),
                                "url": url,
                                "snippet": r.get("body")
                            }
                except Exception as e:
                    print(f"Search failed for query '{query}': {e}")
                    continue

        return list(companies.values())
