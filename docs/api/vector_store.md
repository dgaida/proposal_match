<a id="app.utils.vector_store"></a>

# app.utils.vector\_store

<a id="app.utils.vector_store.VectorStore"></a>

## VectorStore Objects

```python
class VectorStore()
```

Manages semantic vector storage and querying using ChromaDB.

**Attributes**:

- `client` _PersistentClient_ - The ChromaDB client.
- `collection` _Collection_ - The ChromaDB collection for companies.

<a id="app.utils.vector_store.VectorStore.__init__"></a>

#### \_\_init\_\_

```python
def __init__(persist_directory: str = "data/chroma_db")
```

Initializes the vector store with a persistence directory.

**Arguments**:

- `persist_directory` _str_ - Path to store the ChromaDB database.

<a id="app.utils.vector_store.VectorStore.add_company_vector"></a>

#### add\_company\_vector

```python
def add_company_vector(company_id: str, text: str,
                       metadata: Dict[str, Any]) -> None
```

Upserts a company's vector embedding and metadata.

**Arguments**:

- `company_id` _str_ - Unique ID (usually URL).
- `text` _str_ - Semantic text to be embedded.
- `metadata` _Dict[str, Any]_ - Associated metadata for filtering.

<a id="app.utils.vector_store.VectorStore.query_companies"></a>

#### query\_companies

```python
def query_companies(
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
```

Queries the vector store for similar companies using semantic search.

**Arguments**:

- `query_text` _str_ - The search query text.
- `n_results` _int_ - Number of results to return.
- `where` _Optional[Dict[str, Any]]_ - Metadata filters for the search.
- `where_document` _Optional[Dict[str, Any]]_ - Document/keyword filters (e.g., {"$contains": "AI"}).


**Returns**:

  Dict[str, Any]: Results from ChromaDB including ids, documents, and metadatas.
