# Installation

This guide describes the installation of the Funding Research App for local development and production use.

## Prerequisites

- **Python**: Version 3.10 or higher.  
- **Git**: For cloning the repository.  
- (Optional) **Ollama**: For local LLM support.  

## Local Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/dgaida/proposal_match.git
   cd proposal_match
   ```

2. Create a virtual environment and activate it:  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in editable mode:  
   ```bash
   pip install -e .
   ```

## Starting the Application

Run the following command to start the Streamlit app:
```bash
streamlit run app/main.py
```

The app will be accessible by default at `http://localhost:8501`.

## Deployment on Render.com

The app is pre-configured for easy deployment on [Render](https://render.com):

1. **Create a New Web Service**: Select your GitHub repository.  
2. **Runtime**: Python.  
3. **Build Command**: `pip install -r requirements.txt`.  
4. **Start Command**: `streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`.  
5. **Disk (Optional)**: For persistent data (SQLite and ChromaDB), attach a [Render Disk](https://render.com/docs/disks).  
