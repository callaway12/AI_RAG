"""
Document Chunker for FDA documents
Handles text splitting with metadata preservation
"""
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

from .config import CHUNK_SIZE, CHUNK_OVERLAP


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to approximate count
        return len(text) // 4


class FDADocumentChunker:
    """Chunker optimized for FDA regulatory documents"""

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Use RecursiveCharacterTextSplitter with FDA-relevant separators
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 4,  # Approximate chars from tokens
            chunk_overlap=chunk_overlap * 4,
            length_function=len,
            separators=[
                "\n\n\n",  # Major section breaks
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentence breaks
                ", ",      # Clause breaks
                " ",       # Word breaks
                ""
            ]
        )

    def chunk_document(self, document: Document) -> List[Document]:
        """Split a document into chunks while preserving metadata"""

        # Skip if document is too short
        if len(document.page_content) < 100:
            return [document]

        # Split the document
        chunks = self.text_splitter.split_documents([document])

        # Add chunk-specific metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)
            chunk.metadata["chunk_size"] = len(chunk.page_content)

        return chunks

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split multiple documents into chunks"""

        all_chunks = []

        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        return all_chunks


def create_chunker(
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> FDADocumentChunker:
    """Factory function to create a chunker"""
    return FDADocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


if __name__ == "__main__":
    # Test chunking
    test_doc = Document(
        page_content="This is a test document. " * 500,
        metadata={"source": "test.pdf"}
    )

    chunker = create_chunker()
    chunks = chunker.chunk_document(test_doc)

    print(f"Original doc length: {len(test_doc.page_content)}")
    print(f"Number of chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):
        print(f"Chunk {i}: {len(chunk.page_content)} chars")
