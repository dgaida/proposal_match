<a id="app.services.llm_service"></a>

# app.services.llm\_service

<a id="app.services.llm_service.LLMService"></a>

## LLMService Objects

```python
class LLMService()
```

Service for interacting with various LLM providers using the LLMClient library.

**Attributes**:

- `provider` _str_ - The current LLM provider being used.  
- `api_key` _Optional[str]_ - The API key for the current provider.  
- `llm_model` _Optional[str]_ - The specific model name being used.  
- `available_providers` _Dict[str, str]_ - A dictionary of providers and their API keys.  
- `client` _LLMClient_ - The instance of the LLMClient used for API calls.  

<a id="app.services.llm_service.LLMService.__init__"></a>

#### \_\_init\_\_

```python
def __init__(provider: str = "openai",
             api_key: Optional[str] = None,
             llm_model: Optional[str] = None)
```

Initializes the LLMService with a provider, API key, and model.

**Arguments**:

- `provider` _str_ - The LLM provider to use (e.g., 'openai', 'groq', 'gemini').  
- `api_key` _Optional[str]_ - The API key for the provider.  
- `llm_model` _Optional[str]_ - The specific model name to use.  

<a id="app.services.llm_service.LLMService.chat_completion"></a>

#### chat\_completion

```python
def chat_completion(messages: List[Dict[str, str]]) -> str
```

Sends a chat completion request to the current LLM provider.

**Arguments**:

- `messages` _List[Dict[str, str]]_ - A list of message dictionaries (role and content).  


**Returns**:

- `str` - The text response from the LLM.  

<a id="app.services.llm_service.LLMService.chat_with_fallback"></a>

#### chat\_with\_fallback

```python
def chat_with_fallback(
        messages: List[Dict[str, str]],
        status_callback: Optional[Callable[[str], None]] = None) -> str
```

Sends a chat completion request with fallback to other available providers on failure.

**Arguments**:

- `messages` _List[Dict[str, str]]_ - A list of message dictionaries.  
- `status_callback` _Optional[Callable[[str], None]]_ - Optional callback for status updates.  


**Returns**:

- `str` - The text response from the LLM.  


**Raises**:

- `Exception` - If all available providers fail or no providers are configured.  

<a id="app.services.llm_service.LLMService.extract_structured_data"></a>

#### extract\_structured\_data

```python
def extract_structured_data(
        text: str,
        prompt: str,
        status_callback: Optional[Callable[[str], None]] = None) -> str
```

Uses the LLM to extract structured information from the provided text.

**Arguments**:

- `text` _str_ - The source text to extract data from.  
- `prompt` _str_ - The specific extraction instructions.  
- `status_callback` _Optional[Callable[[str], None]]_ - Optional callback for status updates.  


**Returns**:

- `str` - The extracted data, typically in JSON format as a string.  

<a id="app.services.llm_service.LLMService.switch_config"></a>

#### switch\_config

```python
def switch_config(provider: str,
                  api_key: str,
                  llm_model: Optional[str] = None) -> None
```

Dynamically switches the LLM provider, API key, and model.

**Arguments**:

- `provider` _str_ - The new LLM provider name.  
- `api_key` _str_ - The new API key.  
- `llm_model` _Optional[str]_ - The new model name.  
