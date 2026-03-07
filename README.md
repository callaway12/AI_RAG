# FDA 510(k) RAG System

S-Patch CardioAI (K254255) FDA 피드백 대응을 위한 RAG 시스템

## 설치

```bash
cd /Users/taewankim/Documents/FDA/RAG_DEV

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 패키지 설치
pip install -e .
```

## 환경 설정

`.env` 파일 생성:
```bash
cp .env.example .env
```

API 키 설정:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## 사용법

### 1. 문서 인덱싱 (최초 1회)

```bash
fda-rag index

# 또는 강제 재인덱싱
fda-rag index --force
```

### 2. 검색

```bash
# 기본 검색
fda-rag search "cloud penetration testing"

# 카테고리 필터
fda-rag search "risk analysis" --category cybersecurity

# FINAL 문서만
fda-rag search "lead II" --final-only
```

### 3. 질문 (Claude 분석 포함)

```bash
fda-rag ask "SC-11 Cloud Pen Test 제외 정당화 관련 우리 문서 현황 분석해줘"
```

### 4. FDA 결함 분석

```bash
fda-rag analyze SC-11
fda-rag analyze PT-17
```

### 5. 문서 일관성 체크

```bash
fda-rag consistency cloud
fda-rag consistency "electronic interface"
```

### 6. 클라우드 관련 전체 검색

```bash
fda-rag cloud
```

### 7. 대화형 모드

```bash
fda-rag interactive
```

## FDA 결함 ID 체계

| Prefix | Category | 담당 |
|--------|----------|------|
| DD | Device Description | AI Lead / CTO |
| LB | Labeling | RA |
| SC | Software/Cybersecurity | CTO |
| PT | Performance Testing | AI Lead |
| MN | Minor | RA |

## 예시 쿼리

```bash
# 클라우드 서비스 일관성 체크
fda-rag consistency cloud

# 특정 결함 분석
fda-rag analyze SC-11

# 자유 질문
fda-rag ask "우리 문서에서 Lead II 관련 내용 어디어디에 있어?"
fda-rag ask "Risk Acceptability Matrix가 ISO 14971이랑 뭐가 다른지 분석해줘"
fda-rag ask "Subgroup analysis 관련 현재 데이터 현황 확인해줘"
```

## 파일 구조

```
RAG_DEV/
├── src/
│   ├── __init__.py
│   ├── config.py          # 설정
│   ├── document_loader.py # 문서 로딩 (PDF, DOCX, XLSX, JSON)
│   ├── chunker.py         # 텍스트 청킹
│   ├── vector_store.py    # ChromaDB 벡터 스토어
│   ├── search.py          # 검색 엔진
│   ├── rag_chain.py       # RAG + Claude 체인
│   └── main.py            # CLI 인터페이스
├── data/
│   └── chroma_db/         # 벡터 DB 저장 (인덱싱 후 생성)
├── tests/
├── requirements.txt
├── setup.py
├── .env.example
└── README.md
```

## 문서 카테고리

| Category | 폴더 | 관련 결함 |
|----------|------|----------|
| regulatory | 01, 04, 05, 98 | DD-4, LB-5, MN-1 |
| technical | 02, 07, 09 | DD-1, DD-2, DD-3, SC-14 |
| cybersecurity | 20, 21 | SC-6~SC-13 |
| performance | 18 | PT-15~PT-20 |
| risk | 06, 08, 13 | SC-6, PT-15 |
