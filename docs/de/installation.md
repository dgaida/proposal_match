# Installation

Diese Anleitung beschreibt die Installation der Förderrecherche App für lokale Entwicklung und den produktiven Einsatz.

## Voraussetzungen

- **Python**: Version 3.10 oder höher.  
- **Git**: Zum Klonen des Repositories.  
- (Optional) **Ollama**: Für lokale LLM-Unterstützung.  

## Lokale Installation

1. Klonen Sie das Repository:  
   ```bash
   git clone https://github.com/dgaida/proposal_match.git
   cd proposal_match
   ```

2. Erstellen Sie eine virtuelle Umgebung und aktivieren Sie diese:  
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   ```

3. Installieren Sie die Abhängigkeiten:  
   ```bash
   pip install -r requirements.txt
   ```

4. Installieren Sie das Paket im editierbaren Modus:  
   ```bash
   pip install -e .
   ```

## Starten der Anwendung

Führen Sie den folgenden Befehl aus, um die Streamlit-App zu starten:
```bash
streamlit run app/main.py
```

Die App wird standardmäßig unter `http://localhost:8501` erreichbar sein.

## Deployment auf Render.com

Die App ist für ein einfaches Deployment auf [Render](https://render.com) vorkonfiguriert:

1. **Neuen Web Service erstellen**: Wählen Sie Ihr GitHub-Repository aus.  
2. **Runtime**: Python.  
3. **Build Command**: `pip install -r requirements.txt`.  
4. **Start Command**: `streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`.  
5. **Disk (Optional)**: Für persistente Daten (SQLite und ChromaDB) binden Sie einen [Render Disk](https://render.com/docs/disks) ein.  
