# Configuration

The Funding Research App can be configured via environment variables and directly within the application.

## API Keys and Providers

Configure the LLM provider and the corresponding API key in the app's sidebar. The app supports the following providers:

- **OpenAI**: Requires an `OPENAI_API_KEY`.
- **Groq**: Requires a `GROQ_API_KEY`.
- **Gemini**: Requires a `GEMINI_API_KEY`.
- **Ollama**: Supports local models (e.g., `llama3`).

### Environment Variables

You can also define API keys directly in a `.env` file or as environment variables:
```bash
OPENAI_API_KEY=sk-your-key
GROQ_API_KEY=gsk-your-key
GEMINI_API_KEY=your-key
```

## Database Credentials

To use the FIT database search and LinkedIn integration, you must provide your login credentials:

- **FIT Uni Kassel**: Username and password.
- **LinkedIn**: Username and password (currently restricted).

## Persistent Data Storage

The app stores data in the following directories:

- **SQLite**: `data/companies.db` (Organization metadata).
- **ChromaDB**: `data/chroma_db/` (Vector embeddings for semantic search).
- **Summaries**: `data/summaries/` (Analyzed calls).
- **Proposals**: `data/proposals/` (Generated project proposals).

---

!!! info
    Ensure the `data/` directory is writable to prevent data loss.
