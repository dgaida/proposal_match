<a id="app.services.scraper_service"></a>

# app.services.scraper\_service

<a id="app.services.scraper_service.ScraperService"></a>

## ScraperService Objects

```python
class ScraperService()
```

Service for scraping and cleaning web content.

**Attributes**:

- `timeout` _int_ - The HTTP request timeout in seconds.

<a id="app.services.scraper_service.ScraperService.__init__"></a>

#### \_\_init\_\_

```python
def __init__(timeout: int = 30)
```

Initializes the ScraperService with a timeout.

**Arguments**:

- `timeout` _int_ - The HTTP request timeout in seconds.

<a id="app.services.scraper_service.ScraperService.fetch_page_content"></a>

#### fetch\_page\_content

```python
def fetch_page_content(url: str) -> Optional[dict]
```

Fetches the text content of a given URL and follows redirects.

**Arguments**:

- `url` _str_ - The URL to fetch content from.


**Returns**:

- `Optional[dict]` - A dictionary containing 'text' and 'final_url', or None on failure.
