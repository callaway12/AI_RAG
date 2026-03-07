"""
FDA RAG System - Streamlit Web UI
S-Patch CardioAI (K254255) FDA Feedback Response System
"""
import streamlit as st
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import VECTOR_STORE_PATH
from src.vector_store import create_vector_store
from src.search import create_search_engine
from src.rag_chain import FDARAGChain
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from src.config import ANTHROPIC_API_KEY

# Page config
st.set_page_config(
    page_title="FDA RAG System - S-Patch CardioAI",
    page_icon="🏥",
    layout="wide"
)

# FDA Deficiency categories
FDA_DEFICIENCIES = {
    "DD-1": "ECG Input Validation",
    "DD-2": "Lead II Nomenclature",
    "DD-3": "Sampling Rate (64-512Hz)",
    "DD-4": "Substantial Equivalence",
    "LB-5": "Integration Guide",
    "SC-6": "Risk Analysis Issues",
    "SC-7": "SBOM EOS/EOL",
    "SC-8": "CVE Remediation",
    "SC-9": "Unresolved Anomalies",
    "SC-10": "Cybersecurity Controls",
    "SC-11": "Penetration Testing (Cloud)",
    "SC-12": "Cybersecurity Labeling",
    "SC-13": "Cybersecurity Mgmt Plan",
    "SC-14": "Interoperability",
    "PT-15": "Human Factors (URRA)",
    "PT-16": "EC57/IEC 60601 Reports",
    "PT-17": "ML Validation",
    "PT-18": "Multiple Output Validation",
    "PT-19": "Signal Quality Rejection",
    "PT-20": "HR/HRV Statistics",
    "MN-1": "Prescription Statement"
}


@st.cache_resource
def load_rag_system():
    """Load RAG system components (cached)"""
    store = create_vector_store()
    search_engine = create_search_engine(store)

    # Create LLM with conversation support
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        anthropic_api_key=ANTHROPIC_API_KEY,
        max_tokens=4096
    )

    return store, search_engine, llm


def get_conversation_response(llm, search_engine, query: str, history: list) -> str:
    """Get response with conversation context"""

    # Search for relevant documents
    results = search_engine.search(query, k=10)

    if not results:
        return "관련 문서를 찾을 수 없습니다."

    # Format documents
    docs_text = ""
    for i, r in enumerate(results[:8], 1):
        docs_text += f"""
### Document {i}: {r.source}
- Category: {r.category}
- Page: {r.metadata.get('page_number', 'N/A')}

```
{r.content[:1500]}
```
"""

    # Build conversation history
    history_text = ""
    for msg in history[-6:]:  # Last 6 messages for context
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"\n{role}: {msg['content'][:500]}\n"

    # System prompt
    system_prompt = """You are an expert FDA regulatory affairs specialist helping analyze 510(k) submission documents for S-Patch CardioAI (K254255).

Your role:
1. Analyze FDA feedback (AI Letter deficiencies) and find relevant documentation
2. Identify gaps between FDA requirements and current documentation
3. Suggest specific remediation actions

Always respond in Korean when the user asks in Korean.
Always cite specific documents, page numbers, and sections.
Clearly distinguish between "FDA 요구사항" vs "현재 문서 상태".

Format responses with clear headers:
## FDA 요구사항
## 현재 문서 현황
## 갭 분석
## 대응 방안
## 참조 문서
"""

    # Build prompt with history
    prompt = f"""{system_prompt}

## 이전 대화 내용
{history_text}

## 검색된 관련 문서
{docs_text}

## 현재 질문
{query}

위 문서들을 바탕으로 질문에 답변해주세요. 이전 대화 맥락을 고려하여 답변하세요.
"""

    response = llm.invoke(prompt)
    return response.content


def main():
    # Header
    st.title("🏥 FDA RAG System")
    st.markdown("**S-Patch CardioAI (K254255)** FDA 510(k) 피드백 대응 시스템")

    # Load system
    try:
        store, search_engine, llm = load_rag_system()
        stats = store.get_collection_stats()
        st.sidebar.success(f"✅ 인덱싱된 문서: {stats['total_documents']:,} 청크")
    except Exception as e:
        st.error(f"시스템 로드 실패: {e}")
        st.info("먼저 `fda-rag index` 명령으로 문서를 인덱싱하세요.")
        return

    # Sidebar
    st.sidebar.header("FDA Deficiencies")
    st.sidebar.markdown("클릭하면 분석 시작")

    # Quick deficiency buttons
    selected_deficiency = None
    cols = st.sidebar.columns(2)

    for i, (def_id, def_name) in enumerate(FDA_DEFICIENCIES.items()):
        col = cols[i % 2]
        if col.button(f"{def_id}", key=def_id, help=def_name):
            selected_deficiency = def_id

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 빠른 검색")
    quick_topics = ["cloud service", "penetration test", "risk analysis", "lead II", "sampling rate"]
    for topic in quick_topics:
        if st.sidebar.button(f"🔍 {topic}", key=f"quick_{topic}"):
            st.session_state.messages.append({
                "role": "user",
                "content": f"{topic} 관련 문서 현황 분석해줘"
            })

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Handle deficiency button click
    if selected_deficiency:
        def_name = FDA_DEFICIENCIES[selected_deficiency]
        st.session_state.messages.append({
            "role": "user",
            "content": f"{selected_deficiency} ({def_name}) 관련 우리 문서 현황 분석해줘"
        })

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("질문을 입력하세요... (예: SC-11 Cloud Pen Test 관련 문서 분석해줘)"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("문서 분석 중..."):
                response = get_conversation_response(
                    llm,
                    search_engine,
                    prompt,
                    st.session_state.messages[:-1]  # Exclude current message
                )
            st.markdown(response)

        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Process any pending deficiency analysis
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_msg = st.session_state.messages[-1]["content"]
        if any(d in last_msg for d in FDA_DEFICIENCIES.keys()):
            with st.chat_message("assistant"):
                with st.spinner("FDA 결함 분석 중..."):
                    response = get_conversation_response(
                        llm,
                        search_engine,
                        last_msg,
                        st.session_state.messages[:-1]
                    )
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🗑️ 대화 초기화"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        st.markdown(f"**문서:** {stats['total_documents']:,} 청크")
    with col3:
        st.markdown("**모델:** Claude Sonnet")


if __name__ == "__main__":
    main()
