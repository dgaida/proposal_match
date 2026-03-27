# Research Funding and Collaboration App

A comprehensive tool to analyze research calls, find funding opportunities, and manage company collaborations with AI-powered insights.

[![Version](https://img.shields.io/github/v/tag/dgaida/proposal_match?label=version)](https://github.com/dgaida/proposal_match/tags)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code Quality](https://github.com/dgaida/proposal_match/actions/workflows/lint.yml/badge.svg)](https://github.com/dgaida/proposal_match/actions/workflows/lint.yml)
[![Tests](https://github.com/dgaida/proposal_match/actions/workflows/tests.yml/badge.svg)](https://github.com/dgaida/proposal_match/actions/workflows/tests.yml)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/dgaida/proposal_match/graphs/commit-activity)
![Last commit](https://img.shields.io/github/last-commit/dgaida/proposal_match)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## Features

1.  **Research Call Analysis**: Extract and visualize key data (topic, deadline, budget, etc.) from any research call URL.
2.  **FIT Uni Kassel Search**: Search the [FIT Uni Kassel database](https://fit.uni-kassel.de) directly from the app and get AI-powered summaries of relevant calls.
3.  **Company Indexing**: Index company information from URLs. The app crawls websites to extract metadata (SME status, location, industry) and semantic information (summary, products).
4.  **Hybrid Matching**: Match indexed companies to specific research calls using a combination of SQL filtering and semantic vector search (ChromaDB).
5.  **External Discovery**: Search the internet for new potential partners and index them with one click.
6.  **LinkedIn Integration**: Fetch 1st-degree LinkedIn contacts, match them to research calls, and generate personalized outreach messages.
7.  **Configurable Limits**: Set custom limits for LinkedIn contact retrieval and recursive folder indexing to optimize performance.

## Installation

### Prerequisites
- Python 3.10+
- (Optional) [Ollama](https://ollama.ai/) for local LLM support

### Local Setup
1. Clone the repository.
2. Install dependencies and the package:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
3. Run the application:
   ```bash
   streamlit run app/main.py
   ```

## Configuration
Configure your API keys (OpenAI, Groq, or Gemini) and platform credentials (FIT, LinkedIn) directly in the sidebar of the application.

## Deployment on Render.com

This app is configured for easy deployment on [Render](https://render.com).

1.  **Create a New Web Service**: Select your GitHub repository.
2.  **Runtime**: Python.
3.  **Build Command**: `pip install -r requirements.txt`.
4.  **Start Command**: `streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`.
5.  **Environment Variables**:
    -   Add `PORT` (Render usually provides this automatically).
    -   You can also pre-set API keys as environment variables (e.g., `OPENAI_API_KEY`).
6.  **Disk (Optional)**: For persistent data (SQLite and ChromaDB), you can attach a [Render Disk](https://render.com/docs/disks) and point the storage paths in `app/utils/db_manager.py` and `app/utils/vector_store.py` to the mount point.

## Tech Stack
- **Frontend**: Streamlit
- **LLM**: `llm-client` (supporting OpenAI, Groq, Gemini, Ollama)
- **Database**: SQLite (Metadata) & ChromaDB (Vector Search)
- **Scraping**: BeautifulSoup4 & httpx
- **Discovery**: DuckDuckGo Search
- **Networking**: `linkedin_api`

## License
MIT
