"""
Configuration for FDA RAG System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
FDA_DOCS_PATH = Path(os.getenv("FDA_DOCS_PATH", "/Users/taewankim/Documents/FDA"))
VECTOR_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", BASE_DIR / "data" / "chroma_db"))

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Embedding settings
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072

# Chunking settings
CHUNK_SIZE = 1000  # tokens
CHUNK_OVERLAP = 150  # tokens

# Search settings
TOP_K = 10  # Number of results to return
HYBRID_ALPHA = 0.7  # Weight for vector search (1-alpha for BM25)

# Document types to process
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".json", ".txt", ".md"}

# Directories to skip
SKIP_DIRS = {"RAG_DEV", ".git", "__pycache__", "99. Archived (REMOVED)"}

# FDA Deficiency categories for routing
DEFICIENCY_CATEGORIES = {
    "DD": "Device Description",
    "LB": "Labeling",
    "SC": "Software/Cybersecurity",
    "PT": "Performance Testing",
    "MN": "Minor"
}

# Document category mapping based on folder names
FOLDER_TO_CATEGORY = {
    "01. Cover Letter": "regulatory",
    "02. Comprehensive Device Description": "technical",
    "04. Substantial Equivalence": "regulatory",
    "05. IFU": "regulatory",
    "06. Documentation Level": "regulatory",
    "07. Software Description": "technical",
    "08. Risk Management": "risk",
    "09. Software Documents": "technical",
    "13. Software Unresolved": "technical",
    "18. Performance Evaluation": "performance",
    "20. Software Bill of Materials": "cybersecurity",
    "21. Cybersecurity": "cybersecurity",
    "98. 510(k) Summary": "regulatory",
}
