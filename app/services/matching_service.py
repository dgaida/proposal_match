import json
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
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
        """
        companies = []
        with DDGS() as ddgs:
            results = ddgs.text(f"Companies working on {topic}", max_results=10)
            for r in results:
                companies.append({
                    "name": r.get("title"),
                    "url": r.get("href"),
                    "snippet": r.get("body")
                })
        return companies
