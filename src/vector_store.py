"""
Vector Store management using ChromaDB
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from tqdm import tqdm

from .config import (
    VECTOR_STORE_PATH,
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    TOP_K,
)


class FDAVectorStore:
    """Vector store for FDA documents using ChromaDB"""

    def __init__(
        self,
        persist_directory: Path = VECTOR_STORE_PATH,
        collection_name: str = "fda_documents"
    ):
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY
        )

        # Initialize or load vector store
        self.vector_store = None
        self._initialize_store()

    def _initialize_store(self):
        """Initialize or load the vector store"""
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Check if store exists
        if (self.persist_directory / "chroma.sqlite3").exists():
            print(f"Loading existing vector store from {self.persist_directory}")
            self.vector_store = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
        else:
            print(f"Creating new vector store at {self.persist_directory}")
            self.vector_store = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )

    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> int:
        """Add documents to the vector store"""

        if not documents:
            print("No documents to add")
            return 0

        total_added = 0

        # Process in batches
        batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]

        iterator = tqdm(batches, desc="Adding to vector store") if show_progress else batches

        for batch in iterator:
            try:
                self.vector_store.add_documents(batch)
                total_added += len(batch)
            except Exception as e:
                print(f"Error adding batch: {e}")
                # Try adding one by one
                for doc in batch:
                    try:
                        self.vector_store.add_documents([doc])
                        total_added += 1
                    except Exception as e2:
                        print(f"Error adding document: {e2}")

        print(f"Added {total_added} documents to vector store")
        return total_added

    def search(
        self,
        query: str,
        k: int = TOP_K,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents"""

        if filter:
            results = self.vector_store.similarity_search(
                query,
                k=k,
                filter=filter
            )
        else:
            results = self.vector_store.similarity_search(query, k=k)

        return results

    def search_with_scores(
        self,
        query: str,
        k: int = TOP_K,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """Search for similar documents with similarity scores"""

        if filter:
            results = self.vector_store.similarity_search_with_score(
                query,
                k=k,
                filter=filter
            )
        else:
            results = self.vector_store.similarity_search_with_score(query, k=k)

        return results

    def search_by_category(
        self,
        query: str,
        category: str,
        k: int = TOP_K
    ) -> List[Document]:
        """Search within a specific document category"""
        return self.search(query, k=k, filter={"category": category})

    def search_final_only(
        self,
        query: str,
        k: int = TOP_K
    ) -> List[Document]:
        """Search only in FINAL submission documents"""
        return self.search(query, k=k, filter={"submission_stage": "FINAL"})

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        collection = self.vector_store._collection

        return {
            "total_documents": collection.count(),
            "persist_directory": str(self.persist_directory),
            "collection_name": self.collection_name,
        }

    def delete_collection(self):
        """Delete the entire collection"""
        self.vector_store.delete_collection()
        print(f"Deleted collection: {self.collection_name}")


def create_vector_store(
    persist_directory: Path = VECTOR_STORE_PATH,
    collection_name: str = "fda_documents"
) -> FDAVectorStore:
    """Factory function to create a vector store"""
    return FDAVectorStore(
        persist_directory=persist_directory,
        collection_name=collection_name
    )


if __name__ == "__main__":
    # Test vector store
    store = create_vector_store()
    stats = store.get_collection_stats()
    print(f"Vector store stats: {stats}")
