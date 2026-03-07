"""
Document Loader for FDA documents
Supports: PDF, DOCX, XLSX, JSON, TXT, MD
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from tqdm import tqdm

# Document loaders
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    TextLoader,
)
from langchain.schema import Document

from .config import (
    FDA_DOCS_PATH,
    SUPPORTED_EXTENSIONS,
    SKIP_DIRS,
    FOLDER_TO_CATEGORY,
)


@dataclass
class LoadedDocument:
    """Represents a loaded document with metadata"""
    content: str
    metadata: Dict[str, Any]
    source_path: Path


def get_category_from_path(file_path: Path) -> str:
    """Determine document category from file path"""
    path_str = str(file_path)

    for folder_prefix, category in FOLDER_TO_CATEGORY.items():
        if folder_prefix in path_str:
            return category

    # Check for submission stage
    if "FINAL_" in path_str:
        return "final_submission"
    elif "DRAFT_" in path_str:
        return "draft"
    elif "EDIT_" in path_str:
        return "edit"
    elif "POST_" in path_str:
        return "post_submission"
    elif "Cybersecurity" in path_str or "SBOM" in path_str:
        return "cybersecurity"
    elif "Performance" in path_str or "Clinical" in path_str:
        return "performance"

    return "general"


def extract_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from file path and name"""
    relative_path = file_path.relative_to(FDA_DOCS_PATH) if FDA_DOCS_PATH in file_path.parents else file_path

    # Determine submission stage
    path_str = str(file_path)
    if "FINAL_" in path_str:
        stage = "FINAL"
    elif "DRAFT_" in path_str:
        stage = "DRAFT"
    elif "EDIT_" in path_str:
        stage = "EDIT"
    elif "POST_" in path_str:
        stage = "POST"
    else:
        stage = "CURRENT"

    # Extract version if present (e.g., Rev.1.1, Ver 1.2)
    import re
    version_match = re.search(r'[Rr]ev\.?(\d+\.?\d*)|[Vv]er\.?\s*(\d+\.?\d*)', file_path.name)
    version = version_match.group(1) or version_match.group(2) if version_match else None

    return {
        "source": str(file_path),
        "relative_path": str(relative_path),
        "filename": file_path.name,
        "extension": file_path.suffix.lower(),
        "category": get_category_from_path(file_path),
        "submission_stage": stage,
        "version": version,
        "file_size": file_path.stat().st_size if file_path.exists() else 0,
    }


def load_pdf(file_path: Path) -> List[Document]:
    """Load PDF document"""
    try:
        loader = PyPDFLoader(str(file_path))
        pages = loader.load()

        metadata = extract_metadata(file_path)
        for i, page in enumerate(pages):
            page.metadata.update(metadata)
            page.metadata["page_number"] = i + 1

        return pages
    except Exception as e:
        print(f"Error loading PDF {file_path}: {e}")
        return []


def load_docx(file_path: Path) -> List[Document]:
    """Load DOCX document"""
    try:
        loader = Docx2txtLoader(str(file_path))
        docs = loader.load()

        metadata = extract_metadata(file_path)
        for doc in docs:
            doc.metadata.update(metadata)

        return docs
    except Exception as e:
        print(f"Error loading DOCX {file_path}: {e}")
        return []


def load_excel(file_path: Path) -> List[Document]:
    """Load Excel document"""
    try:
        loader = UnstructuredExcelLoader(str(file_path))
        docs = loader.load()

        metadata = extract_metadata(file_path)
        for doc in docs:
            doc.metadata.update(metadata)

        return docs
    except Exception as e:
        print(f"Error loading Excel {file_path}: {e}")
        return []


def load_json(file_path: Path) -> List[Document]:
    """Load JSON document (especially SBOM files)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        metadata = extract_metadata(file_path)

        # Special handling for SBOM files
        if "SBOM" in file_path.name or "spdx" in str(data).lower():
            metadata["document_type"] = "SBOM"

            # Extract packages and vulnerabilities
            docs = []

            # Main document
            content = json.dumps(data, indent=2, ensure_ascii=False)
            docs.append(Document(page_content=content[:10000], metadata=metadata))

            # Extract individual packages if present
            packages = data.get("packages", [])
            for pkg in packages[:50]:  # Limit to first 50 packages
                pkg_content = json.dumps(pkg, indent=2, ensure_ascii=False)
                pkg_metadata = metadata.copy()
                pkg_metadata["package_name"] = pkg.get("name", "unknown")
                docs.append(Document(page_content=pkg_content, metadata=pkg_metadata))

            return docs
        else:
            content = json.dumps(data, indent=2, ensure_ascii=False)
            return [Document(page_content=content, metadata=metadata)]

    except Exception as e:
        print(f"Error loading JSON {file_path}: {e}")
        return []


def load_text(file_path: Path) -> List[Document]:
    """Load text/markdown document"""
    try:
        loader = TextLoader(str(file_path), encoding='utf-8')
        docs = loader.load()

        metadata = extract_metadata(file_path)
        for doc in docs:
            doc.metadata.update(metadata)

        return docs
    except Exception as e:
        print(f"Error loading text {file_path}: {e}")
        return []


def load_document(file_path: Path) -> List[Document]:
    """Load a document based on its extension"""
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext == ".docx":
        return load_docx(file_path)
    elif ext in {".xlsx", ".xls"}:
        return load_excel(file_path)
    elif ext == ".json":
        return load_json(file_path)
    elif ext in {".txt", ".md"}:
        return load_text(file_path)
    else:
        return []


def discover_documents(root_path: Path = FDA_DOCS_PATH) -> List[Path]:
    """Discover all supported documents in the FDA directory"""
    documents = []

    for file_path in root_path.rglob("*"):
        # Skip directories in SKIP_DIRS
        if any(skip_dir in str(file_path) for skip_dir in SKIP_DIRS):
            continue

        # Check if file has supported extension
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            documents.append(file_path)

    return sorted(documents)


def load_all_documents(
    root_path: Path = FDA_DOCS_PATH,
    show_progress: bool = True
) -> List[Document]:
    """Load all documents from the FDA directory"""

    file_paths = discover_documents(root_path)
    print(f"Found {len(file_paths)} documents to process")

    all_documents = []

    iterator = tqdm(file_paths, desc="Loading documents") if show_progress else file_paths

    for file_path in iterator:
        docs = load_document(file_path)
        all_documents.extend(docs)

    print(f"Loaded {len(all_documents)} document chunks")
    return all_documents


if __name__ == "__main__":
    # Test document loading
    docs = load_all_documents()
    print(f"\nTotal documents loaded: {len(docs)}")

    # Show sample
    if docs:
        print(f"\nSample document metadata:")
        print(docs[0].metadata)
