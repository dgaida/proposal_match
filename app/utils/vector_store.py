import os
import chromadb
from typing import Dict, Any, Optional

class VectorStore:
    def __init__(self, persist_directory: str = "data/chroma_db"):
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="companies")

    def add_company_vector(self, company_id: str, text: str, metadata: Dict[str, Any]):
        """
        Adds a new company to the vector store.
        """
        self.collection.upsert(
            documents=[text],
            metadatas=[metadata],
            ids=[str(company_id)]
        )

    def query_companies(self, query_text: str, n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Queries the vector store for similar companies.
        """
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
