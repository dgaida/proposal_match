<a id="app.services.fit_service"></a>

# app.services.fit\_service

<a id="app.services.fit_service.FITService"></a>

## FITService Objects

```python
class FITService()
```

Service for interacting with the FIT Uni Kassel research funding database.

**Attributes**:

- `base_url` _str_ - The base URL for the FIT API.  
- `llm_service` _LLMService_ - The LLM service for filtering and summarizing.  
- `auth_url` _str_ - The URL for Keycloak authentication.  
- `client` _httpx.Client_ - The HTTP client for making API requests.  

<a id="app.services.fit_service.FITService.__init__"></a>

#### \_\_init\_\_

```python
def __init__(llm_service: LLMService,
             base_url: str = "https://fit.uni-kassel.de/api")
```

Initializes the FITService.

**Arguments**:

- `llm_service` _LLMService_ - The LLM service for analysis.  
- `base_url` _str_ - The API base URL.  

<a id="app.services.fit_service.FITService.login"></a>

#### login

```python
def login(username: str,
          password: str,
          status_callback: Optional[Callable[[str], None]] = None) -> bool
```

Authenticates with Keycloak to obtain an access token.

**Arguments**:

- `username` _str_ - The FIT username.  
- `password` _str_ - The FIT password.  
- `status_callback` _Optional[Callable[[str], None]]_ - Callback for status updates.  


**Returns**:

- `bool` - True if login is successful, False otherwise.  

<a id="app.services.fit_service.FITService.search_calls"></a>

#### search\_calls

```python
def search_calls(
    query: str,
    status_callback: Optional[Callable[[str], None]] = None
) -> List[Dict[str, Any]]
```

Searches for research calls on FIT and uses LLM for relevance filtering.

**Arguments**:

- `query` _str_ - The search query.  
- `status_callback` _Optional[Callable[[str], None]]_ - Callback for status updates.  


**Returns**:

  List[Dict[str, Any]]: A list of relevant research call documents.

<a id="app.services.fit_service.FITService.summarize_results"></a>

#### summarize\_results

```python
def summarize_results(
        results: List[Dict[str, Any]],
        status_callback: Optional[Callable[[str], None]] = None) -> str
```

Generates a summary of research funding results using an LLM.

**Arguments**:

- `results` _List[Dict[str, Any]]_ - The search results to summarize.  
- `status_callback` _Optional[Callable[[str], None]]_ - Callback for status updates.  


**Returns**:

- `str` - A formatted summary of the results in German.  
