"""
Setup script for FDA RAG System
"""
from setuptools import setup, find_packages

setup(
    name="fda-rag",
    version="0.1.0",
    description="FDA 510(k) RAG System for S-Patch CardioAI",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "langchain-openai>=0.0.5",
        "langchain-anthropic>=0.1.0",
        "chromadb>=0.4.22",
        "pypdf>=3.17.0",
        "python-docx>=1.1.0",
        "openpyxl>=3.1.2",
        "unstructured>=0.12.0",
        "openai>=1.12.0",
        "tiktoken>=0.5.2",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.0",
        "rich>=13.7.0",
        "rank-bm25>=0.2.2",
        "click>=8.1.7",
    ],
    entry_points={
        "console_scripts": [
            "fda-rag=src.main:main",
        ],
    },
)
