import json
from typing import List, Dict, Any, Optional, Callable
from ddgs import DDGS
from app.services.llm_service import LLMService
from app.utils.db_manager import DBManager, Company
from app.utils.vector_store import VectorStore
from app.utils.json_utils import parse_llm_json_list
from app.models.models import MatchResultModel, ProposalModel, ResearchCallModel


class MatchingService:
    """Service for matching research calls with organizations in the database.

    Attributes:
        llm_service (LLMService): LLM service for analysis and generation.
        db_manager (DBManager): Manager for SQLite database interactions.
        vector_store (VectorStore): Manager for ChromaDB vector store.
    """

    def __init__(
        self, llm_service: LLMService, db_manager: DBManager, vector_store: VectorStore
    ):
        """Initializes the MatchingService.

        Args:
            llm_service (LLMService): The LLM service for logic.
            db_manager (DBManager): The database manager.
            vector_store (VectorStore): The vector store manager.
        """
        self.llm_service = llm_service
        self.db_manager = db_manager
        self.vector_store = vector_store

    def suggest_research_topics(
        self,
        call_data: Dict[str, Any],
        user_context: str = "",
        matched_companies: List[Dict[str, Any]] = [],
    ) -> List[str]:
        """Suggests 5 project ideas for a research call and potential partners.

        Args:
            call_data (Dict[str, Any]): Data about the research call.
            user_context (str): The background of the user.
            matched_companies (List[Dict[str, Any]]): A list of companies that match the call.

        Returns:
            List[str]: A list of suggested research topics and roles.
        """
        companies_info = "\n".join(
            [
                f"- {c['name']} (Industry: {c['industry']}): {c['summary']}"
                for c in matched_companies
            ]
        )

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
            {
                "role": "system",
                "content": "You are an expert in research and development strategy.",
            },
            {"role": "user", "content": prompt},
        ]
        response = self.llm_service.chat_completion(messages)
        # Simplified parsing for the suggestion list
        return [
            line.strip("- ").strip("12345. ")
            for line in response.splitlines()
            if line.strip()
        ]

    def generate_multiple_matching_queries(
        self, context_data: Any, n: int = 5
    ) -> List[str]:
        """Generates multiple diverse semantic search queries in German.

        Args:
            context_data (Any): Data about the research call or a manual query string.
            n (int): Number of queries to generate.

        Returns:
            List[str]: A list of query strings for vector search.
        """
        context_str = (
            json.dumps(context_data)
            if isinstance(context_data, dict)
            else str(context_data)
        )
        prompt = f"""
        Given the following context, generate {n} diverse semantic search queries in GERMAN to find matching companies in a vector database.
        The companies in the database are described in German.
        Each query should be 1-2 sentences long and focus on different aspects of the context (technical, application-oriented, strategic).
        Return only the queries, one per line, without numbering or bullets.

        Context: {context_str}
        """
        messages = [
            {
                "role": "system",
                "content": "You are an expert in research funding and technical matchmaking. You respond only in German.",
            },
            {"role": "user", "content": prompt},
        ]
        response = self.llm_service.chat_completion(messages)
        return [
            line.strip("- ").strip() for line in response.splitlines() if line.strip()
        ]

    def rephrase_query(self, query: str) -> str:
        """Rephrases a manual query to be optimal for semantic search in German.

        Args:
            query (str): The user's original search term.

        Returns:
            str: The rephrased and expanded query.
        """
        prompt = f"""
        Rephrase and expand the following search query to be optimal for a semantic search in a vector database containing German company profiles.
        Include synonyms and related technical terms in GERMAN.
        RESPOND ONLY WITH THE REPHRASED QUERY IN GERMAN.

        Original query: {query}
        """
        messages = [
            {
                "role": "system",
                "content": "You are an expert in information retrieval and semantic search.",
            },
            {"role": "user", "content": prompt},
        ]
        return self.llm_service.chat_completion(messages).strip('" \n')

    def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        keywords: Optional[str] = None,
        limit: int = 10,
    ) -> List[MatchResultModel]:
        """Finds matching organizations using a hybrid vector-metadata search.

        Args:
            query (str): The semantic search query.
            filters (Optional[Dict[str, Any]]): Filters for country, state, org type, etc.
            keywords (Optional[str]): Keywords for document-level filtering.
            limit (int): Maximum number of results to return.

        Returns:
            List[MatchResultModel]: A list of matching organization models including relevance scores.
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

        # Prepare keyword filter
        where_doc = None
        if keywords:
            where_doc = {"$contains": keywords}

        # Step 2: Semantic search in ChromaDB with pre-filtering
        print("Hybrid Search Execution:")
        print(f"  Query: {query}")
        print(f"  Filters: {where_filter}")
        print(f"  Keywords: {keywords}")

        if filters:
            session = self.db_manager.Session()
            db_q = session.query(Company)
            if filters.get("state"):
                db_q = db_q.filter(Company.state == filters["state"])
            if filters.get("country"):
                db_q = db_q.filter(Company.country == filters["country"])
            if filters.get("org_type"):
                db_q = db_q.filter(Company.org_type == filters["org_type"])
            if filters.get("kmu_status") is not None:
                db_q = db_q.filter(Company.kmu_status == filters["kmu_status"])
            count = db_q.count()
            print(f"  Companies matching metadata filters in SQLite: {count}")
            session.close()

        vector_results = self.vector_store.query_companies(
            query_text=query,
            n_results=limit,
            where=where_filter,
            where_document=where_doc,
        )

        # Extract the results from the vector store response
        # Normalize IDs (strip trailing slashes) to ensure match with SQLite
        raw_ids = vector_results.get("ids", [[]])[0]
        company_ids = [url.rstrip("/") for url in raw_ids]
        distances = vector_results.get("distances", [[]])[0]

        # Step 3: Fetch full metadata from SQLite for the results
        # We use Company.url.in_(company_ids) to perform a batch retrieval using the SQLAlchemy IN operator.
        # This efficiently fetches all Company records whose URL matches any of the IDs returned by the vector search.
        print(f"Vector search returned {len(company_ids)} company IDs.")
        session = self.db_manager.Session()
        # To be absolutely robust, we search for IDs both with and without trailing slashes
        query_ids = company_ids + [url + "/" for url in company_ids]
        results = session.query(Company).filter(Company.url.in_(query_ids)).all()
        print(f"Successfully retrieved {len(results)} companies from SQLite.")

        # Maintain vector search order (relevance) and include scores
        # Store results using normalized URL as key
        id_to_result = {r.url.rstrip("/"): r for r in results}
        id_to_distance = dict(zip(company_ids, distances))

        final_results = []
        for url in company_ids:
            if url in id_to_result:
                r = id_to_result[url]
                dist = id_to_distance.get(url, 1.0)
                # Convert distance to a relevance score (0.0 to 1.0)
                # ChromaDB distances are often L2; 1/(1+dist) is a common heuristic
                relevance = 1.0 / (1.0 + dist)

                final_results.append(
                    MatchResultModel(
                        name=r.name,
                        url=r.url,
                        state=r.state,
                        city=r.city,
                        country=r.country,
                        org_type=r.org_type,
                        industry=r.industry,
                        summary=r.summary,
                        employees_count=r.employees_count,
                        kmu_status=r.kmu_status,
                        relevance=relevance,
                    )
                )

        session.close()
        return final_results

    def generate_detailed_proposals(
        self,
        call_data: ResearchCallModel | Dict[str, Any],
        user_context: str = "",
        matched_companies: List[MatchResultModel] = [],
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> List[ProposalModel]:
        """Generates 5 detailed project proposals with missing partner discovery.

        Args:
            call_data (ResearchCallModel | Dict[str, Any]): Data about the research call.
            user_context (str): The background of the user.
            matched_companies (List[MatchResultModel]): A list of companies that already match the call.
            status_callback (Optional[Callable[[str], None]]): Callback for status updates.

        Returns:
            List[ProposalModel]: A list of detailed project proposals.
        """
        if status_callback:
            status_callback(
                "Generiere Projektideen und Suchanfragen für fehlende Partner..."
            )

        companies_info = "\n".join(
            [
                f"- {c.name} (Branche: {c.industry}): {c.summary}"
                for c in matched_companies
            ]
        )
        call_json = (
            call_data.model_dump()
            if isinstance(call_data, ResearchCallModel)
            else call_data
        )

        prompt = f"""
        Basierend auf dem folgenden Forschungs-Call und dem Profil des Nutzers, erstelle 5 konkrete Projektideen (Vorschläge).
        Berücksichtige dabei die bereits vorhandenen Partner aus der Datenbank.

        Nutzer-Profil:
        {user_context}

        Call-Daten:
        {json.dumps(call_json)}

        Bereits gefundene Partner aus der Datenbank:
        {companies_info}

        Erstelle für jede der 5 Projektideen ein JSON-Objekt mit folgendem Aufbau:
        {{
            "title": "Titel des Projekts",
            "description": "Detaillierte Projektbeschreibung auf Deutsch (ca. 100-200 Wörter).",
            "existing_partners": [
                {{
                    "name": "Name des Unternehmens",
                    "role": "Spezifische Rolle dieses Partners in diesem Projekt"
                }}
            ],
            "missing_partners_search": [
                {{
                    "type_description": "Beschreibung des benötigten Partners (z.B. KMU für Sensorik)",
                    "filters": {{
                        "country": "Deutschland",
                        "org_type": "Unternehmen",
                        "kmu_status": true
                    }},
                    "queries": ["Semantische Suchanfrage 1", "Semantische Suchanfrage 2"],
                    "keywords": "Stichwort für die Suche",
                    "intended_role": "Geplante Rolle für diesen Partner im Projekt"
                }}
            ]
        }}

        WICHTIG:
        - Wenn ein KMU benötigt wird, setze kmu_status: true und org_type: "Unternehmen".
        - Wenn ein allgemeines Unternehmen benötigt wird, setze kmu_status: false (oder lass es weg) und org_type: "Unternehmen".
        - Erstelle bis zu 5 Suchanfragen insgesamt pro Projektidee für fehlende Partner.
        - Antworte ausschließlich mit einer JSON-Liste dieser 5 Objekte.
        """

        messages = [
            {
                "role": "system",
                "content": "Du bist ein Experte für Forschungsförderung und Konsortialbildung. Du antwortest nur in validem JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.llm_service.chat_completion(messages)
        proposals_data = parse_llm_json_list(response)
        if not proposals_data:
            return []

        final_proposals = []
        for i, prop_dict in enumerate(proposals_data):
            try:
                # Basic validation with model_validate (without newly_found_partners yet)
                prop = ProposalModel.model_validate(prop_dict)
            except Exception as e:
                print(f"Proposal validation failed for item {i}: {e}")
                continue

            if status_callback:
                status_callback(
                    f"Suche Partner für Projekt {i + 1}/{len(proposals_data)}: {prop.title}..."
                )

            found_partners = []
            seen_urls = set()

            for missing_search in prop.missing_partners_search:
                print(f"  - Missing Partner Request: {missing_search.type_description}")
                for q in missing_search.queries:
                    matches = self.hybrid_search(
                        q,
                        filters=missing_search.filters,
                        keywords=missing_search.keywords,
                        limit=3,
                    )
                    for m in matches:
                        if m.url not in seen_urls:
                            # We might want to store project_role somewhere,
                            # but currently MatchResultModel doesn't have it.
                            # Proposal integration is handled via the newly_found_partners list.
                            found_partners.append(m)
                            seen_urls.add(m.url)

            found_partners.sort(key=lambda x: x.relevance, reverse=True)
            prop.newly_found_partners = found_partners
            final_proposals.append(prop)

        return final_proposals

    def generate_match_justification(
        self,
        call_data: ResearchCallModel | Dict[str, Any],
        matched_companies: List[MatchResultModel],
    ) -> List[MatchResultModel]:
        """Generates a German justification for each matched organization.

        Args:
            call_data (ResearchCallModel | Dict[str, Any]): Data about the research call.
            matched_companies (List[MatchResultModel]): The list of matched organizations.

        Returns:
            List[MatchResultModel]: The original list of companies updated with a 'justification' field.
        """
        if not matched_companies:
            return []

        call_json = (
            call_data.model_dump()
            if isinstance(call_data, ResearchCallModel)
            else call_data
        )
        results_with_justification = []
        for company in matched_companies:
            prompt = f"""
            Given the following research call and the information about an organization,
            explain in 2-3 sentences why this organization is a particularly good match for this call.
            BE BRIEF AND SPECIFIC. RESPOND IN GERMAN.

            Call: {json.dumps(call_json)}
            Organization: {company.name} ({company.org_type}) - {company.summary}
            """
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert in research collaborations.",
                },
                {"role": "user", "content": prompt},
            ]
            justification = self.llm_service.chat_completion(messages)
            company.justification = justification
            results_with_justification.append(company)

        return results_with_justification

    def search_internet_for_companies(self, topic: str) -> List[Dict[str, str]]:
        """Searches the web for new companies matching a research topic.

        Args:
            topic (str): The target topic or sector for discovery.

        Returns:
            List[Dict[str, str]]: A list of discovered company URLs and snippets.
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
            {
                "role": "system",
                "content": "You are an expert at information retrieval and search engine optimization.",
            },
            {"role": "user", "content": query_prompt},
        ]

        try:
            llm_response = self.llm_service.chat_completion(messages)
            queries = [
                q.strip("- ").strip("123. ")
                for q in llm_response.splitlines()
                if q.strip()
            ]
            # Ensure we have at least the original topic if LLM fails
            if not queries:
                queries = [topic]
        except Exception as e:
            print(f"Error generating search queries: {e}")
            queries = [topic]

        # Step 2: Execute searches and collect results
        companies = {}  # Use dict to deduplicate by URL
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
                                "snippet": r.get("body"),
                            }
                except Exception as e:
                    print(f"Search failed for query '{query}': {e}")
                    continue

        return list(companies.values())
