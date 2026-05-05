# Architecture

The Funding Research App is a modular Streamlit application that utilizes various specialized services.

## System Overview

The app is based on a service-oriented architecture. The user interface (`app/main.py`) acts as the central orchestrator and calls the corresponding services.

```mermaid
graph TD
    UI[Streamlit UI] --> AS[AnalyzerService]
    UI --> FS[FITService]
    UI --> IS[IndexingService]
    UI --> MS[MatchingService]
    UI --> LS[LinkedInService]

    AS --> LLM[LLMService]
    FS --> FIT[FIT API]
    IS --> SS[ScraperService]
    IS --> DB[DBManager]
    IS --> VS[VectorStore]
    MS --> DB
    MS --> VS
    MS --> LLM
    LS --> LI[LinkedIn API]
    LS --> LLM

    subgraph "Data Storage"
        DB --- SQLite[(SQLite)]
        VS --- Chroma[(ChromaDB)]
    end
```

## Data Flow

The typical data flow for a call analysis looks like this:

```mermaid
sequenceDiagram
    participant User as User
    participant UI as Streamlit UI
    participant AS as AnalyzerService
    participant LLM as LLMService
    participant DB as DBManager

    User->>UI: Enter URL
    UI->>AS: Analyze URL
    AS->>LLM: Send text content
    LLM-->>AS: Extract metadata
    AS-->>UI: Display summary
    UI->>DB: Save result
```

## Core Components

### Services (`app/services/`)  
- **AnalyzerService**: Extraction of structured data from research calls.  
- **FITService**: Interface to the University of Kassel research database.  
- **IndexingService**: Crawling and indexing of websites.  
- **LinkedInService**: Contact management and outreach.  
- **LLMService**: Abstraction layer for various LLM providers.  
- **MatchingService**: Performing hybrid searches.  
- **ScraperService**: Fetching and cleaning web content.  

### Utilities (`app/utils/`)  
- **DBManager**: Management of the SQLite database.  
- **VectorStore**: Management of the ChromaDB vector database.  
- **Translations**: Support for multi-language support.  
- **GeoUtils**: Geocoding of company locations.  
