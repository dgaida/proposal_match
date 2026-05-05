<a id="app.services.linkedin_service"></a>

# app.services.linkedin\_service

<a id="app.services.linkedin_service.LinkedInService"></a>

## LinkedInService Objects

```python
class LinkedInService()
```

Service for LinkedIn integration and contact matching.

**Attributes**:

- `llm_service` _LLMService_ - LLM service for analysis and generation.  
- `api` _Optional[Linkedin]_ - LinkedIn API instance or None if not initialized.  

<a id="app.services.linkedin_service.LinkedInService.__init__"></a>

#### \_\_init\_\_

```python
def __init__(llm_service: LLMService,
             username: Optional[str] = None,
             password: Optional[str] = None)
```

Initializes the LinkedInService.

**Arguments**:

- `llm_service` _LLMService_ - The LLM service for logic.  
- `username` _Optional[str]_ - LinkedIn account username.  
- `password` _Optional[str]_ - LinkedIn account password.  

<a id="app.services.linkedin_service.LinkedInService.get_first_degree_contacts"></a>

#### get\_first\_degree\_contacts

```python
def get_first_degree_contacts(
    limit: int = -1,
    status_callback: Optional[Callable[[str], None]] = None
) -> List[Dict[str, Any]]
```

Fetches 1st-degree contacts from the LinkedIn account.

**Arguments**:

- `limit` _int_ - Maximum number of contacts to fetch. Defaults to -1 (no limit).  
- `status_callback` _Optional[Callable[[str], None]]_ - Callback for status updates.  


**Returns**:

  List[Dict[str, Any]]: A list of contact dictionaries.

<a id="app.services.linkedin_service.LinkedInService.generate_outreach_message"></a>

#### generate\_outreach\_message

```python
def generate_outreach_message(contact_name: str, company_name: str,
                              call_data: Dict[str, Any]) -> str
```

Generates a professional outreach message via LLM.

**Arguments**:

- `contact_name` _str_ - Full name of the contact.  
- `company_name` _str_ - The organization they are associated with.  
- `call_data` _Dict[str, Any]_ - Data about the research call for context.  


**Returns**:

- `str` - The generated outreach text.  

<a id="app.services.linkedin_service.LinkedInService.find_matching_contacts_for_call"></a>

#### find\_matching\_contacts\_for\_call

```python
def find_matching_contacts_for_call(
        contacts: List[Dict[str, Any]],
        call_data: Dict[str, Any],
        status_callback: Optional[Callable[[str],
                                           None]] = None) -> Dict[str, Any]
```

Analyzes a list of LinkedIn contacts to find matches for a research call.

**Arguments**:

- `contacts` _List[Dict[str, Any]]_ - The list of LinkedIn contacts to analyze.  
- `call_data` _Dict[str, Any]_ - The research call details.  
- `status_callback` _Optional[Callable[[str], None]]_ - Callback for status updates.  


**Returns**:

  Dict[str, Any]: A dictionary containing 'matches' (objects), 'identified_names', and 'criteria'.
