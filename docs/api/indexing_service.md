<a id="app.services.indexing_service"></a>

# app.services.indexing\_service

<a id="app.services.indexing_service.IndexingService"></a>

## IndexingService Objects

```python
class IndexingService()
```

Service for indexing company information from web links and local files.

**Attributes**:

- `llm_service` _LLMService_ - LLM service for information extraction.  
- `db_manager` _DBManager_ - Manager for SQLite database storage.  
- `vector_store` _VectorStore_ - Manager for ChromaDB vector storage.  
- `scraper_service` _ScraperService_ - Service for web content scraping.  

<a id="app.services.indexing_service.IndexingService.__init__"></a>

#### \_\_init\_\_

```python
def __init__(llm_service: LLMService, db_manager: DBManager,
             vector_store: VectorStore)
```

Initializes the IndexingService.

**Arguments**:

- `llm_service` _LLMService_ - The LLM service for analysis.  
- `db_manager` _DBManager_ - The database manager.  
- `vector_store` _VectorStore_ - The vector store manager.  

<a id="app.services.indexing_service.IndexingService.index_companies_from_links"></a>

#### index\_companies\_from\_links

```python
def index_companies_from_links(links: List[str]) -> int
```

Processes and indexes a list of company website URLs.

**Arguments**:

- `links` _List[str]_ - A list of URLs to index.  


**Returns**:

- `int` - The total count of newly indexed companies.  

<a id="app.services.indexing_service.IndexingService.index_from_folder"></a>

#### index\_from\_folder

```python
def index_from_folder(
        folder_path: str,
        limit: int = 25,
        status_callback: Optional[Callable[[str], None]] = None) -> List[str]
```

Indexes company URLs found in .url files within a local directory.

**Arguments**:

- `folder_path` _str_ - The directory path to scan.  
- `limit` _int_ - Maximum number of new companies to index.  
- `status_callback` _Optional[Callable[[str], None]]_ - Callback for status updates.  


**Returns**:

- `List[str]` - A list of URLs that were successfully indexed.  
