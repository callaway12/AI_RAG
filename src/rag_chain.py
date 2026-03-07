"""
RAG Chain for FDA document Q&A
Uses Claude for response generation
"""
import os
from typing import List, Optional
from langchain.schema import Document
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate

from .search import FDASearchEngine, SearchResult
from .config import ANTHROPIC_API_KEY


# System prompt for FDA document analysis
FDA_SYSTEM_PROMPT = """You are an expert FDA regulatory affairs specialist helping analyze 510(k) submission documents for S-Patch CardioAI (K254255).

Your role is to:
1. Analyze FDA feedback (AI Letter deficiencies) and find relevant documentation
2. Identify gaps between FDA requirements and current documentation
3. Suggest specific remediation actions

When responding:
- Always cite specific documents, page numbers, and sections
- Clearly distinguish between "what FDA requires" vs "what we have"
- Highlight inconsistencies between documents if found
- Provide actionable recommendations

Document categories:
- regulatory: 510(k) summary, substantial equivalence, IFU, labeling
- technical: device description, software description, algorithm documentation
- cybersecurity: security plans, SBOM, penetration testing, threat modeling
- performance: clinical testing, EC57 reports, validation studies
- risk: risk management, hazard analysis, FMEA

FDA Deficiency ID prefixes:
- DD: Device Description
- LB: Labeling
- SC: Software/Cybersecurity
- PT: Performance Testing
- MN: Minor deficiency
"""

ANALYSIS_PROMPT_TEMPLATE = """Based on the following retrieved documents, analyze the query and provide a comprehensive response.

## Query
{query}

## Retrieved Documents
{documents}

## Instructions
1. First, identify which FDA deficiency (if any) this relates to
2. Summarize what relevant information exists in the current documents
3. Identify any gaps or missing information
4. If inconsistencies are found between documents, highlight them
5. Provide specific recommendations for addressing the issue

Format your response as:

## FDA 요구사항
[What FDA is asking for, if applicable]

## 현재 문서 현황
### 발견된 관련 문서
[List of relevant documents with specific references]

### 현재 상태 요약
[Summary table or bullet points]

## 갭 분석
[What's missing or inconsistent]

## 대응 방안
[Specific recommendations]

## 참조 문서
[Document names, pages, sections]
"""


class FDARAGChain:
    """RAG chain for FDA document analysis"""

    def __init__(
        self,
        search_engine: FDASearchEngine,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.search_engine = search_engine

        # Initialize Claude
        self.llm = ChatAnthropic(
            model=model,
            anthropic_api_key=ANTHROPIC_API_KEY,
            max_tokens=4096
        )

        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", FDA_SYSTEM_PROMPT),
            ("human", ANALYSIS_PROMPT_TEMPLATE)
        ])

    def _format_documents(self, results: List[SearchResult]) -> str:
        """Format search results for the prompt"""
        formatted = []

        for i, result in enumerate(results, 1):
            doc_info = f"""
### Document {i}: {result.source}
- Category: {result.category}
- Relevance Score: {result.relevance_score:.3f}
- Page: {result.metadata.get('page_number', 'N/A')}
- Version: {result.metadata.get('version', 'N/A')}
- Submission Stage: {result.metadata.get('submission_stage', 'N/A')}

Content:
```
{result.content}
```
"""
            formatted.append(doc_info)

        return "\n".join(formatted)

    def query(
        self,
        query: str,
        k: int = 10,
        category_filter: Optional[str] = None,
        final_only: bool = False
    ) -> str:
        """
        Process a query through the RAG chain

        Args:
            query: User query
            k: Number of documents to retrieve
            category_filter: Filter by document category
            final_only: Only search FINAL documents
        """

        # Search for relevant documents
        results = self.search_engine.search(
            query,
            k=k,
            category_filter=category_filter,
            final_only=final_only
        )

        if not results:
            return "관련 문서를 찾을 수 없습니다. 검색어를 다시 확인해주세요."

        # Format documents
        formatted_docs = self._format_documents(results)

        # Generate response
        messages = self.prompt.format_messages(
            query=query,
            documents=formatted_docs
        )

        response = self.llm.invoke(messages)

        return response.content

    def analyze_deficiency(self, deficiency_id: str) -> str:
        """
        Analyze a specific FDA deficiency

        Args:
            deficiency_id: FDA deficiency ID (e.g., "SC-11", "PT-17c")
        """
        query = f"FDA deficiency {deficiency_id} 관련 문서 현황 분석"
        return self.query(query)

    def check_consistency(self, topic: str, keywords: List[str]) -> str:
        """
        Check document consistency for a specific topic

        Args:
            topic: Topic to check (e.g., "cloud service")
            keywords: Related keywords
        """

        # Search for all keywords
        all_results = self.search_engine.search_for_inconsistencies(topic, keywords)

        # Flatten results
        flat_results = []
        for keyword, results in all_results.items():
            flat_results.extend(results)

        # Remove duplicates based on source
        seen = set()
        unique_results = []
        for r in flat_results:
            if r.source not in seen:
                seen.add(r.source)
                unique_results.append(r)

        if not unique_results:
            return f"'{topic}' 관련 문서를 찾을 수 없습니다."

        # Format and query
        formatted_docs = self._format_documents(unique_results[:15])

        consistency_query = f"""
다음 문서들에서 '{topic}' 관련 내용의 일관성을 분석해주세요.

특히 다음을 확인:
1. 각 문서에서 '{topic}'에 대해 어떻게 기술하고 있는지
2. 문서 간 모순되는 내용이 있는지
3. 누락된 정보가 있는지

키워드: {', '.join(keywords)}
"""

        messages = self.prompt.format_messages(
            query=consistency_query,
            documents=formatted_docs
        )

        response = self.llm.invoke(messages)
        return response.content


def create_rag_chain(search_engine: FDASearchEngine) -> FDARAGChain:
    """Factory function to create a RAG chain"""
    return FDARAGChain(search_engine)
