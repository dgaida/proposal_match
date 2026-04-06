# Konfiguration

Die Förderrecherche App kann über Umgebungsvariablen und direkt in der Anwendung konfiguriert werden.

## API-Schlüssel und Anbieter

Stellen Sie in der Seitenleiste der App den LLM-Anbieter und den entsprechenden API-Schlüssel ein. Die App unterstützt folgende Anbieter:

- **OpenAI**: Erfordert einen `OPENAI_API_KEY`.
- **Groq**: Erfordert einen `GROQ_API_KEY`.
- **Gemini**: Erfordert einen `GEMINI_API_KEY`.
- **Ollama**: Unterstützt lokale Modelle (z.B. `llama3`).

### Umgebungsvariablen

Sie können die API-Schlüssel auch direkt in einer `.env`-Datei oder als Umgebungsvariablen definieren:
```bash
OPENAI_API_KEY=sk-your-key
GROQ_API_KEY=gsk-your-key
GEMINI_API_KEY=your-key
```

## Datenbank-Anmeldedaten

Um die Suche in der FIT-Datenbank und die LinkedIn-Integration zu nutzen, müssen Sie Ihre Anmeldedaten angeben:

- **FIT Uni Kassel**: Benutzername und Passwort.
- **LinkedIn**: Benutzername und Passwort (derzeit eingeschränkt).

## Persistente Datenspeicherung

Die App speichert Daten in folgenden Verzeichnissen:

- **SQLite**: `data/companies.db` (Metadaten der Organisationen).
- **ChromaDB**: `data/chroma_db/` (Vektoreinbettungen für semantische Suche).
- **Summaries**: `data/summaries/` (Analysierte Ausschreibungen).
- **Proposals**: `data/proposals/` (Generierte Projektvorschläge).

---

!!! info
    Stellen Sie sicher, dass das Verzeichnis `data/` beschreibbar ist, um Datenverlust zu vermeiden.
