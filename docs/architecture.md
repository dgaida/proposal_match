# Architecture Documentation

The Funding Research and Collaboration App is a modular Streamlit application with several core services and utility modules.

## Architecture Overview
The application follows a service-oriented architecture, where the UI (app/main.py) interacts with various specialized service classes.

### Services (app/services/)  
- **AnalyzerService**: Handles AI analysis and extraction of structured data from research call text.  
- **FITService**: Manages authentication and search functionality for the FIT Uni Kassel database.  
- **IndexingService**: Crawls and indexes company websites, extracting metadata and semantic information.  
- **LinkedInService**: Fetches 1st-degree contacts and matches them with research calls.  
- **LLMService**: A generic client supporting multiple LLM providers (OpenAI, Groq, Gemini, Ollama).  
- **MatchingService**: Performs hybrid search (metadata + vector) and suggests project topics.  
- **ScraperService**: Handles fetching and cleaning content from external URLs.  

### Utilities (app/utils/)  
- **DBManager**: Manages the SQLite database for company metadata and user context.  
- **VectorStore**: Manages the ChromaDB vector database for semantic search.  
- **Translations**: A centralized translation dictionary and helper function for multi-language support.  
- **FileUtils**: Common file handling utilities (e.g., calculating file age).  

### Data Storage  
- **data/summaries/**: AI-generated research call summaries in Markdown format.  
- **data/queries/**: Cached semantic search queries for calls.  
- **data/fit_cache.json**: Cached search results from the FIT database.  
- **SQLite Database**: `data/funding.db` (contains company metadata).  
- **ChromaDB**: `data/chroma_db/` (contains vector embeddings).  

## Technical Stack  
- **Frontend**: Streamlit  
- **LLM Client**: `llm-client` (custom fork supporting OpenAI, Groq, Gemini, Ollama)  
- **Database**: SQLite (Metadata) & ChromaDB (Vector)  
- **Networking**: `httpx`, `BeautifulSoup4`, `linkedin_api`  
- **Internet Search**: `ddgs` (DuckDuckGo Search)  
- **Environment**: Python 3.10+  
