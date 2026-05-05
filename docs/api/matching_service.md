<a id="app.services.matching_service"></a>

# app.services.matching\_service

<a id="app.services.matching_service.MatchingService"></a>

## MatchingService Objects

```python
class MatchingService()
```

Service for matching research calls with organizations in the database.

**Attributes**:

- `llm_service` _LLMService_ - LLM service for analysis and generation.  
- `db_manager` _DBManager_ - Manager for SQLite database interactions.  
- `vector_store` _VectorStore_ - Manager for ChromaDB vector store.  

<a id="app.services.matching_service.MatchingService.__init__"></a>

#### \_\_init\_\_

```python
def __init__(llm_service: LLMService, db_manager: DBManager,
             vector_store: VectorStore)
```

Initializes the MatchingService.

**Arguments**:

- `llm_service` _LLMService_ - The LLM service for logic.  
- `db_manager` _DBManager_ - The database manager.  
- `vector_store` _VectorStore_ - The vector store manager.  

<a id="app.services.matching_service.MatchingService.suggest_research_topics"></a>

#### suggest\_research\_topics

```python
def suggest_research_topics(
        call_data: Dict[str, Any],
        user_context: str = "",
        matched_companies: List[Dict[str, Any]] = []) -> List[str]
```

Suggests 5 project ideas for a research call and potential partners.

**Arguments**:

- `call_data` _Dict[str, Any]_ - Data about the research call.  
- `user_context` _str_ - The background of the user.  
- `matched_companies` _List[Dict[str, Any]]_ - A list of companies that match the call.  


**Returns**:

- `List[str]` - A list of suggested research topics and roles.  

<a id="app.services.matching_service.MatchingService.generate_multiple_matching_queries"></a>

#### generate\_multiple\_matching\_queries

```python
def generate_multiple_matching_queries(context_data: Any,
                                       n: int = 5) -> List[str]
```

Generates multiple diverse semantic search queries in German.

**Arguments**:

- `context_data` _Any_ - Data about the research call or a manual query string.  
- `n` _int_ - Number of queries to generate.  


**Returns**:

- `List[str]` - A list of query strings for vector search.  

<a id="app.services.matching_service.MatchingService.rephrase_query"></a>

#### rephrase\_query

```python
def rephrase_query(query: str) -> str
```

Rephrases a manual query to be optimal for semantic search in German.

**Arguments**:

- `query` _str_ - The user's original search term.  


**Returns**:

- `str` - The rephrased and expanded query.  

<a id="app.services.matching_service.MatchingService.hybrid_search"></a>

#### hybrid\_search

```python
def hybrid_search(query: str,
                  filters: Optional[Dict[str, Any]] = None,
                  keywords: Optional[str] = None,
                  limit: int = 10) -> List[Dict[str, Any]]
```

Finds matching organizations using a hybrid vector-metadata search.

**Arguments**:

- `query` _str_ - The semantic search query.  
- `filters` _Optional[Dict[str, Any]]_ - Filters for country, state, org type, etc.  
- `keywords` _Optional[str]_ - Keywords for document-level filtering.  
- `limit` _int_ - Maximum number of results to return.  


**Returns**:

  List[Dict[str, Any]]: A list of matching organization metadata including relevance scores.

<a id="app.services.matching_service.MatchingService.generate_detailed_proposals"></a>

#### generate\_detailed\_proposals

```python
def generate_detailed_proposals(
    call_data: Dict[str, Any],
    user_context: str = "",
    matched_companies: List[Dict[str, Any]] = [],
    status_callback: Optional[Callable[[str], None]] = None
) -> List[Dict[str, Any]]
```

Generates 5 detailed project proposals with missing partner discovery.

**Arguments**:

- `call_data` _Dict[str, Any]_ - Data about the research call.  
- `user_context` _str_ - The background of the user.  
- `matched_companies` _List[Dict[str, Any]]_ - A list of companies that already match the call.  
- `status_callback` _Optional[Callable[[str], None]]_ - Callback for status updates.  


**Returns**:

  List[Dict[str, Any]]: A list of detailed project proposals.

<a id="app.services.matching_service.MatchingService.generate_match_justification"></a>

#### generate\_match\_justification

```python
def generate_match_justification(
        call_data: Dict[str, Any],
        matched_companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```

Generates a German justification for each matched organization.

**Arguments**:

- `call_data` _Dict[str, Any]_ - Data about the research call.  
- `matched_companies` _List[Dict[str, Any]]_ - The list of matched organizations.  


**Returns**:

  List[Dict[str, Any]]: The original list of companies updated with a 'justification' field.

<a id="app.services.matching_service.MatchingService.search_internet_for_companies"></a>

#### search\_internet\_for\_companies

```python
def search_internet_for_companies(topic: str) -> List[Dict[str, str]]
```

Searches the web for new companies matching a research topic.

**Arguments**:

- `topic` _str_ - The target topic or sector for discovery.  


**Returns**:

  List[Dict[str, str]]: A list of discovered company URLs and snippets.
