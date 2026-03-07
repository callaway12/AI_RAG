"""
Search Engine for FDA RAG System
Combines vector search with BM25 for hybrid search
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from langchain.schema import Document
from rank_bm25 import BM25Okapi

from .vector_store import FDAVectorStore
from .config import TOP_K, HYBRID_ALPHA, DEFICIENCY_CATEGORIES


@dataclass
class SearchResult:
    """Represents a search result with metadata"""
    content: str
    source: str
    category: str
    relevance_score: float
    metadata: Dict[str, Any]

    def __str__(self):
        return f"[{self.category}] {self.source}\nScore: {self.relevance_score:.3f}\n{self.content[:200]}..."


class FDASearchEngine:
    """Hybrid search engine combining vector search and BM25"""

    def __init__(self, vector_store: FDAVectorStore):
        self.vector_store = vector_store
        self.bm25_index = None
        self.bm25_documents = None

    def parse_deficiency_id(self, query: str) -> Optional[Tuple[str, str]]:
        """Extract FDA deficiency ID from query (e.g., SC-11, PT-17)"""
        match = re.search(r'(DD|LB|SC|PT|MN)-(\d+[a-z]?)', query, re.IGNORECASE)
        if match:
            prefix = match.group(1).upper()
            number = match.group(2)
            category = DEFICIENCY_CATEGORIES.get(prefix, "Unknown")
            return (f"{prefix}-{number}", category)
        return None

    def get_category_filter(self, deficiency_id: str) -> Optional[str]:
        """Get document category filter based on deficiency ID"""
        prefix = deficiency_id[:2].upper()

        category_map = {
            "DD": "technical",      # Device Description
            "LB": "regulatory",     # Labeling
            "SC": "cybersecurity",  # Software/Cybersecurity
            "PT": "performance",    # Performance Testing
            "MN": "regulatory",     # Minor
        }

        return category_map.get(prefix)

    def search(
        self,
        query: str,
        k: int = TOP_K,
        category_filter: Optional[str] = None,
        final_only: bool = False
    ) -> List[SearchResult]:
        """
        Perform hybrid search on FDA documents

        Args:
            query: Search query
            k: Number of results to return
            category_filter: Filter by document category
            final_only: Only search FINAL submission documents
        """

        # Check for deficiency ID in query
        deficiency_info = self.parse_deficiency_id(query)
        if deficiency_info and not category_filter:
            _, category_filter = deficiency_info[0][:2], self.get_category_filter(deficiency_info[0])

        # Build filter
        filter_dict = {}
        if category_filter:
            filter_dict["category"] = category_filter
        if final_only:
            filter_dict["submission_stage"] = "FINAL"

        # Vector search
        if filter_dict:
            vector_results = self.vector_store.search_with_scores(
                query, k=k * 2, filter=filter_dict
            )
        else:
            vector_results = self.vector_store.search_with_scores(query, k=k * 2)

        # Convert to SearchResult
        results = []
        for doc, score in vector_results:
            results.append(SearchResult(
                content=doc.page_content,
                source=doc.metadata.get("relative_path", doc.metadata.get("source", "Unknown")),
                category=doc.metadata.get("category", "general"),
                relevance_score=1 - score,  # Convert distance to similarity
                metadata=doc.metadata
            ))

        # Sort by relevance and return top k
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:k]

    def search_for_inconsistencies(
        self,
        topic: str,
        keywords: List[str],
        k: int = 20
    ) -> Dict[str, List[SearchResult]]:
        """
        Search for a topic across all documents to find inconsistencies

        Args:
            topic: The topic to search for (e.g., "cloud service")
            keywords: Related keywords to search
            k: Number of results per keyword
        """

        all_results = {}

        # Search for each keyword
        for keyword in keywords:
            query = f"{topic} {keyword}"
            results = self.search(query, k=k)
            all_results[keyword] = results

        return all_results

    def search_cloud_references(self) -> Dict[str, List[SearchResult]]:
        """
        Special search to find all cloud-related references
        Useful for SC-11, SC-14 deficiencies
        """

        keywords = [
            "cloud",
            "AWS",
            "web server",
            "electronic interface",
            "https",
            "API",
            "nginx",
            "container",
            "deployment",
            "interoperability"
        ]

        return self.search_for_inconsistencies("cloud service", keywords)

    def format_results(
        self,
        results: List[SearchResult],
        show_content: bool = True,
        max_content_length: int = 500
    ) -> str:
        """Format search results for display"""

        if not results:
            return "No results found."

        output = []
        output.append(f"Found {len(results)} relevant documents:\n")

        for i, result in enumerate(results, 1):
            output.append(f"### {i}. {result.source}")
            output.append(f"- Category: {result.category}")
            output.append(f"- Relevance: {result.relevance_score:.3f}")

            if result.metadata.get("page_number"):
                output.append(f"- Page: {result.metadata['page_number']}")
            if result.metadata.get("version"):
                output.append(f"- Version: {result.metadata['version']}")

            if show_content:
                content = result.content[:max_content_length]
                if len(result.content) > max_content_length:
                    content += "..."
                output.append(f"\n```\n{content}\n```\n")

        return "\n".join(output)


def create_search_engine(vector_store: FDAVectorStore) -> FDASearchEngine:
    """Factory function to create a search engine"""
    return FDASearchEngine(vector_store)
