<a id="app.services.analyzer_service"></a>

# app.services.analyzer\_service

<a id="app.services.analyzer_service.AnalyzerService"></a>

## AnalyzerService Objects

```python
class AnalyzerService()
```

Service for analyzing research call text and extracting structured metadata.

**Attributes**:

- `llm_service` _LLMService_ - The LLM service used for extraction.

<a id="app.services.analyzer_service.AnalyzerService.__init__"></a>

#### \_\_init\_\_

```python
def __init__(llm_service: LLMService)
```

Initializes the AnalyzerService.

**Arguments**:

- `llm_service` _LLMService_ - The LLM service to use.

<a id="app.services.analyzer_service.AnalyzerService.analyze_research_call"></a>

#### analyze\_research\_call

```python
def analyze_research_call(
    text: str,
    url: Optional[str] = None,
    status_callback: Optional[Callable[[str], None]] = None
) -> Optional[Dict[str, Any]]
```

Analyzes a research call using LLM to extract key details.

**Arguments**:

- `text` _str_ - The text content of the research call.
- `url` _Optional[str]_ - The source URL of the call.
- `status_callback` _Optional[Callable[[str], None]]_ - Callback for status updates.


**Returns**:

  Optional[Dict[str, Any]]: A dictionary with extracted call details or None if extraction fails.


**Raises**:

- `Exception` - Propagates exceptions from the LLM service.
