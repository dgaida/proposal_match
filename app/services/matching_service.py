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

    def suggest_research_topics(self, call_data: Dict[str, Any], user_context: str = "", matched_companies: List[Dict[str, Any]] = []) -> List[str]:
        """
        Suggests potential research topics based on the call data, user context, and available companies.
        """
        companies_info = "\n".join([f"- {c['name']} (Industry: {c['industry']}): {c['summary']}" for c in matched_companies])

        prompt = f"""
        Given the following research call information and the user's profile, suggest 5 concrete research topics or project ideas.

        User Profile:
        {user_context}

        Call Data:
        {json.dumps(call_data)}

        Available Companies from Database:
        {companies_info}

        For each suggested topic:
        1. State the project idea.
        2. Specifically highlight which company from the 'Available Companies' would fit well for this suggestion and describe their concrete role/contribution.
        3. Identify which types of partners are still missing to form a complete consortium (e.g., SME in sensor technology, large industrial partner for testing, etc. - do not name specific companies, just the sectors/expertise).
        4. Consider the user's profile to decide which role they/their institution already covers.

        Return the topics as a list with the additional information for each.
        """
        messages = [
            {"role": "system", "content": "You are an expert in research and development strategy."},
            {"role": "user", "content": prompt}
        ]
        response = self.llm_service.chat_completion(messages)
        # Simplified parsing for the suggestion list
        return [line.strip("- ").strip("12345. ") for line in response.splitlines() if line.strip()]

    def generate_matching_query(self, call_data: Dict[str, Any]) -> str:
        """
        Generates a semantic search query based on the call data using the LLM.
        """
        prompt = f"""
        Given the following research call, generate a concise semantic search query (1-2 sentences) that can be used to find matching companies in a vector database.
        The query should focus on the technical requirements, research areas, and necessary expertise.
        RESPOND ONLY WITH THE QUERY STRING.

        Call: {json.dumps(call_data)}
        """
        messages = [
            {"role": "system", "content": "You are an expert in research funding and technical matchmaking."},
            {"role": "user", "content": prompt}
        ]
        return self.llm_service.chat_completion(messages).strip('" \n')

    def hybrid_search(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Performs a hybrid search: first filters by metadata in ChromaDB, then performs semantic search on the remaining items.
        """
        # Step 1: Prepare ChromaDB filter
        where_filter = None
        if filters:
            conditions = []
            if filters.get("state"):
                conditions.append({"state": {"$eq": filters["state"]}})
            if filters.get("country"):
                conditions.append({"country": {"$eq": filters["country"]}})
            if filters.get("org_type"):
                conditions.append({"org_type": {"$eq": filters["org_type"]}})
            if filters.get("kmu_status") is not None:
                conditions.append({"kmu_status": {"$eq": filters["kmu_status"]}})

            if len(conditions) == 1:
                where_filter = conditions[0]
            elif len(conditions) > 1:
                where_filter = {"$and": conditions}

        # Step 2: Semantic search in ChromaDB with pre-filtering
        vector_results = self.vector_store.query_companies(query_text=query, n_results=limit, where=where_filter)

        # Extract the results from the vector store response
        company_ids = vector_results.get("ids", [[]])[0]

        # Step 3: Fetch full metadata from SQLite for the results
        session = self.db_manager.Session()
        results = session.query(Company).filter(Company.url.in_(company_ids)).all()

        # Maintain vector search order (relevance)
        id_to_result = {r.url: r for r in results}
        final_results = [id_to_result[url] for url in company_ids if url in id_to_result]

        # Convert to dictionary for easy consumption
        formatted_results = []
        for r in final_results:
            formatted_results.append({
                "name": r.name,
                "url": r.url,
                "state": r.state,
                "city": r.city,
                "country": r.country,
                "org_type": r.org_type,
                "industry": r.industry,
                "summary": r.summary,
                "employees_count": r.employees_count,
                "kmu_status": r.kmu_status
            })

        session.close()
        return formatted_results

    def generate_match_justification(self, call_data: Dict[str, Any], matched_companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates a justification for why each matched company fits the call.
        """
        if not matched_companies:
            return []

        results_with_justification = []
        for company in matched_companies:
            prompt = f"""
            Given the following research call and the information about an organization,
            explain in 2-3 sentences why this organization is a particularly good match for this call.
            BE BRIEF AND SPECIFIC. RESPOND IN GERMAN.

            Call: {json.dumps(call_data)}
            Organization: {company['name']} ({company['org_type']}) - {company['summary']}
            """
            messages = [
                {"role": "system", "content": "You are an expert in research collaborations."},
                {"role": "user", "content": prompt}
            ]
            justification = self.llm_service.chat_completion(messages)
            company_copy = company.copy()
            company_copy['justification'] = justification
            results_with_justification.append(company_copy)

        return results_with_justification

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
