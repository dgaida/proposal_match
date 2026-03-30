import os
import chromadb
from typing import Dict, Any, Optional, Union
from app.models.models import CompanyModel


class VectorStore:
    """Manages semantic vector storage and querying using ChromaDB.

    Attributes:
        client (PersistentClient): The ChromaDB client.
        collection (Collection): The ChromaDB collection for companies.
    """

    def __init__(self, persist_directory: str = "data/chroma_db"):
        """Initializes the vector store with a persistence directory.

        Args:
            persist_directory (str): Path to store the ChromaDB database.
        """
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="companies")

    def add_company_vector(
        self, company_id: str, text: str, metadata: Union[Dict[str, Any], CompanyModel]
    ) -> None:
        """Upserts a company's vector embedding and metadata.

        Args:
            company_id (str): Unique ID (usually URL).
            text (str): Semantic text to be embedded.
            metadata (Union[Dict[str, Any], CompanyModel]): Associated metadata for filtering.
        """
        if isinstance(metadata, CompanyModel):
            metadata = metadata.model_dump()

        self.collection.upsert(
            documents=[text], metadatas=[metadata], ids=[str(company_id)]
        )

    def query_companies(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Queries the vector store for similar companies using semantic search.

        Args:
            query_text (str): The search query text.
            n_results (int): Number of results to return.
            where (Optional[Dict[str, Any]]): Metadata filters for the search.
            where_document (Optional[Dict[str, Any]]): Document/keyword filters (e.g., {"$contains": "AI"}).

        Returns:
            Dict[str, Any]: Results from ChromaDB including ids, documents, and metadatas.
        """
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            where_document=where_document,
        )
