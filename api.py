"""
FDA RAG System - REST API
Claude Code가 직접 호출해서 문서 검색/분석 가능
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.config import VECTOR_STORE_PATH
from src.vector_store import create_vector_store
from src.search import create_search_engine

# Initialize FastAPI
app = FastAPI(
    title="FDA RAG API",
    description="S-Patch CardioAI (K254255) FDA 피드백 대응 시스템 API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG components
store = None
search_engine = None


@app.on_event("startup")
async def startup():
    global store, search_engine
    store = create_vector_store()
    search_engine = create_search_engine(store)
    print(f"✅ RAG System loaded: {store.get_collection_stats()['total_documents']} chunks")


# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    k: int = 10
    category: Optional[str] = None
    final_only: bool = False


class SearchResult(BaseModel):
    content: str
    source: str
    category: str
    relevance_score: float
    page_number: Optional[int] = None
    version: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_found: int


class ConsistencyRequest(BaseModel):
    topic: str
    keywords: List[str]


class DeficiencyInfo(BaseModel):
    id: str
    name: str
    category: str


# API Endpoints

@app.get("/")
async def root():
    return {
        "service": "FDA RAG API",
        "product": "S-Patch CardioAI (K254255)",
        "status": "running",
        "endpoints": [
            "/search - 문서 검색",
            "/search/cloud - 클라우드 관련 전체 검색",
            "/consistency - 일관성 체크",
            "/deficiencies - FDA 결함 목록",
            "/stats - 인덱싱 통계"
        ]
    }


@app.get("/stats")
async def get_stats():
    """벡터 스토어 통계"""
    stats = store.get_collection_stats()
    return {
        "total_chunks": stats["total_documents"],
        "persist_directory": stats["persist_directory"],
        "collection_name": stats["collection_name"]
    }


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    문서 검색

    Claude Code 사용 예시:
    ```
    curl -X POST http://localhost:8520/search \
      -H "Content-Type: application/json" \
      -d '{"query": "cloud penetration testing", "k": 10}'
    ```
    """
    results = search_engine.search(
        query=request.query,
        k=request.k,
        category_filter=request.category,
        final_only=request.final_only
    )

    return SearchResponse(
        query=request.query,
        results=[
            SearchResult(
                content=r.content,
                source=r.source,
                category=r.category,
                relevance_score=r.relevance_score,
                page_number=r.metadata.get("page_number"),
                version=r.metadata.get("version")
            )
            for r in results
        ],
        total_found=len(results)
    )


@app.get("/search/cloud")
async def search_cloud_references():
    """
    클라우드 관련 모든 문서 검색
    SC-11, SC-14 대응에 유용
    """
    keywords = [
        "cloud", "AWS", "web server", "nginx",
        "container", "deployment", "electronic interface",
        "https", "API", "interoperability"
    ]

    all_results = {}
    for keyword in keywords:
        results = search_engine.search(keyword, k=5)
        all_results[keyword] = [
            {
                "source": r.source,
                "category": r.category,
                "content_preview": r.content[:300],
                "relevance_score": r.relevance_score
            }
            for r in results
        ]

    return {
        "topic": "cloud/web service references",
        "keywords_searched": keywords,
        "results_by_keyword": all_results
    }


@app.post("/consistency")
async def check_consistency(request: ConsistencyRequest):
    """
    문서 일관성 체크

    예시: 클라우드 사용 여부가 문서마다 다르게 기술되어 있는지 확인
    """
    all_results = search_engine.search_for_inconsistencies(
        topic=request.topic,
        keywords=request.keywords
    )

    # Deduplicate by source
    seen_sources = set()
    unique_results = []

    for keyword, results in all_results.items():
        for r in results:
            if r.source not in seen_sources:
                seen_sources.add(r.source)
                unique_results.append({
                    "keyword": keyword,
                    "source": r.source,
                    "category": r.category,
                    "content_preview": r.content[:500],
                    "page_number": r.metadata.get("page_number")
                })

    return {
        "topic": request.topic,
        "keywords": request.keywords,
        "documents_found": len(unique_results),
        "results": unique_results
    }


@app.get("/deficiencies")
async def list_deficiencies():
    """FDA AI Letter 결함 목록 (21개)"""
    return {
        "total": 21,
        "major": 20,
        "minor": 1,
        "deficiencies": {
            "Device Description": [
                {"id": "DD-1", "name": "ECG Input Validation", "owner": "AI Lead"},
                {"id": "DD-2", "name": "Lead II Nomenclature", "owner": "CTO"},
                {"id": "DD-3", "name": "Sampling Rate (64-512Hz)", "owner": "AI Lead"},
                {"id": "DD-4", "name": "Substantial Equivalence", "owner": "RA"},
            ],
            "Labeling": [
                {"id": "LB-5", "name": "Integration Guide", "owner": "CTO"},
            ],
            "Software/Cybersecurity": [
                {"id": "SC-6", "name": "Risk Analysis Issues", "owner": "RA"},
                {"id": "SC-7", "name": "SBOM EOS/EOL", "owner": "CTO"},
                {"id": "SC-8", "name": "CVE Remediation", "owner": "CTO"},
                {"id": "SC-9", "name": "Unresolved Anomalies", "owner": "CTO"},
                {"id": "SC-10", "name": "Cybersecurity Controls", "owner": "CTO"},
                {"id": "SC-11", "name": "Penetration Testing (Cloud)", "owner": "CTO"},
                {"id": "SC-12", "name": "Cybersecurity Labeling", "owner": "RA"},
                {"id": "SC-13", "name": "Cybersecurity Mgmt Plan", "owner": "CTO"},
                {"id": "SC-14", "name": "Interoperability", "owner": "CTO"},
            ],
            "Performance Testing": [
                {"id": "PT-15", "name": "Human Factors (URRA)", "owner": "RA"},
                {"id": "PT-16", "name": "EC57/IEC 60601 Reports", "owner": "AI Lead"},
                {"id": "PT-17", "name": "ML Validation", "owner": "AI Lead"},
                {"id": "PT-18", "name": "Multiple Output Validation", "owner": "AI Lead"},
                {"id": "PT-19", "name": "Signal Quality Rejection", "owner": "AI Lead"},
                {"id": "PT-20", "name": "HR/HRV Statistics", "owner": "AI Lead"},
            ],
            "Minor": [
                {"id": "MN-1", "name": "Prescription Statement", "owner": "RA"},
            ]
        }
    }


@app.get("/search/deficiency/{deficiency_id}")
async def search_by_deficiency(deficiency_id: str):
    """
    특정 FDA 결함 관련 문서 검색

    예: /search/deficiency/SC-11
    """
    deficiency_keywords = {
        "DD-1": ["ECG input", "metadata", "error code", "validation"],
        "DD-2": ["Lead II", "lead 2", "electrode", "nomenclature"],
        "DD-3": ["sampling rate", "64Hz", "512Hz", "resampling", "anti-aliasing"],
        "DD-4": ["substantial equivalence", "predicate", "comparison"],
        "LB-5": ["integration guide", "instructions for use", "IFU"],
        "SC-6": ["risk analysis", "ISO 14971", "hazard", "severity", "FMEA"],
        "SC-7": ["SBOM", "end of support", "EOS", "EOL", "component"],
        "SC-8": ["CVE", "vulnerability", "exploit", "remediation"],
        "SC-9": ["unresolved anomalies", "CWE", "bug"],
        "SC-10": ["cybersecurity controls", "authentication", "encryption"],
        "SC-11": ["penetration test", "cloud", "deployment", "scope"],
        "SC-12": ["cybersecurity labeling", "IFU", "user manual"],
        "SC-13": ["cybersecurity management plan", "patch", "update"],
        "SC-14": ["interoperability", "electronic interface", "web server", "API"],
        "PT-15": ["human factors", "URRA", "use-related risk", "critical task"],
        "PT-16": ["EC57", "IEC 60601", "line-by-line", "report"],
        "PT-17": ["ML validation", "subgroup", "demographic", "race", "site"],
        "PT-18": ["confusion matrix", "output validation", "abnormality score"],
        "PT-19": ["signal quality", "rejection", "ungradable"],
        "PT-20": ["heart rate", "HRV", "Bland-Altman", "Deming", "RMSE"],
        "MN-1": ["prescription", "Rx only", "21 CFR 801.109"],
    }

    keywords = deficiency_keywords.get(deficiency_id.upper())
    if not keywords:
        raise HTTPException(status_code=404, detail=f"Unknown deficiency: {deficiency_id}")

    all_results = []
    seen = set()

    for keyword in keywords:
        results = search_engine.search(keyword, k=5)
        for r in results:
            if r.source not in seen:
                seen.add(r.source)
                all_results.append({
                    "matched_keyword": keyword,
                    "source": r.source,
                    "category": r.category,
                    "content": r.content,
                    "page_number": r.metadata.get("page_number"),
                    "version": r.metadata.get("version"),
                    "relevance_score": r.relevance_score
                })

    # Sort by relevance
    all_results.sort(key=lambda x: x["relevance_score"], reverse=True)

    return {
        "deficiency_id": deficiency_id.upper(),
        "keywords_searched": keywords,
        "documents_found": len(all_results),
        "results": all_results[:15]  # Top 15
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8520)
