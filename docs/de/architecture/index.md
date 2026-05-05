# Architektur

Die Förderrecherche App ist eine modulare Streamlit-Anwendung, die verschiedene spezialisierte Dienste nutzt.

## Systemübersicht

Die App basiert auf einer serviceorientierten Architektur. Die Benutzeroberfläche (`app/main.py`) fungiert als zentraler Orchestrator und ruft die entsprechenden Dienste auf.

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

## Datenfluss

Der typische Datenfluss bei einer Ausschreibungsanalyse sieht wie folgt aus:

```mermaid
sequenceDiagram
    participant User as Benutzer
    participant UI as Streamlit UI
    participant AS as AnalyzerService
    participant LLM as LLMService
    participant DB as DBManager

    User->>UI: URL eingeben
    UI->>AS: URL analysieren
    AS->>LLM: Textinhalt senden
    LLM-->>AS: Metadaten extrahieren
    AS-->>UI: Zusammenfassung anzeigen
    UI->>DB: Ergebnis speichern
```

## Kernkomponenten

### Dienste (`app/services/`)  
- **AnalyzerService**: Extraktion strukturierter Daten aus Ausschreibungen.  
- **FITService**: Schnittstelle zur Forschungsdatenbank der Uni Kassel.  
- **IndexingService**: Crawling und Indexierung von Webseiten.  
- **LinkedInService**: Kontaktmanagement und Outreach.  
- **LLMService**: Abstraktionsschicht für verschiedene LLM-Anbieter.  
- **MatchingService**: Durchführung der Hybrid-Suche.  
- **ScraperService**: Abrufen und Bereinigen von Webinhalten.  

### Hilfsprogramme (`app/utils/`)  
- **DBManager**: Verwaltung der SQLite-Datenbank.  
- **VectorStore**: Verwaltung der ChromaDB-Vektordatenbank.  
- **Translations**: Unterstützung für Mehrsprachigkeit.  
- **GeoUtils**: Geokodierung von Firmenstandorten.  
