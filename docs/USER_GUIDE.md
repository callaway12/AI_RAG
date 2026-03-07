# FDA RAG System 사용 설명서

**S-Patch CardioAI (K254255) FDA 510(k) 피드백 대응 시스템**

**문서 버전**: 1.0
**작성일**: 2026-03-07
**대상**: CTO, AI Lead, RA 팀

---

## 1. 시스템 개요

### 1.1 목적
FDA 510(k) 제출 후 받은 AI Letter (Additional Information) 피드백 대응을 위한 AI 기반 문서 검색 및 분석 시스템

### 1.2 주요 기능

| 기능 | 설명 |
|------|------|
| **문서 검색** | 345개 FDA 제출 문서에서 관련 내용 즉시 검색 |
| **갭 분석** | FDA 요구사항 vs 현재 문서 상태 비교 |
| **일관성 체크** | 문서 간 모순/불일치 탐지 (예: 클라우드 사용 여부) |
| **결함 분석** | FDA 결함 21개 항목별 상세 분석 |
| **대화 컨텍스트** | 이전 대화 내용 기억하며 연속 질문 가능 |

### 1.3 지원 문서 형식
- PDF, DOCX, XLSX, XLS, JSON, TXT, MD

### 1.4 현재 인덱싱 현황
- **총 문서**: 332개 파일
- **인덱싱된 청크**: 4,018개
- **커버리지**: Device Description, Cybersecurity, Performance, Risk Management 등

---

## 2. 접속 방법

### 2.1 Web UI (권장)

**URL**: http://localhost:8510

```bash
cd /Users/taewankim/Documents/FDA/RAG_DEV
source venv/bin/activate
streamlit run app.py --server.port 8510
```

### 2.2 CLI (Command Line)

```bash
cd /Users/taewankim/Documents/FDA/RAG_DEV
source venv/bin/activate
fda-rag [명령어]
```

---

## 3. Web UI 사용법

### 3.1 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  🏥 FDA RAG System                                          │
│  S-Patch CardioAI (K254255) FDA 510(k) 피드백 대응 시스템    │
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│  [사이드바]       │  [채팅 영역]                             │
│                  │                                          │
│  📋 Device       │  User: SC-11 분석해줘                    │
│    Description   │                                          │
│    DD-1: ECG...  │  Assistant: ## FDA 요구사항              │
│    DD-2: Lead... │  SC-11은 Penetration Testing에서...      │
│                  │                                          │
│  📋 Software/    │  ## 현재 문서 현황                        │
│    Cybersecurity │  ...                                     │
│    SC-6: Risk... │                                          │
│    SC-11: Pen... │  ## 갭 분석                              │
│                  │  ...                                     │
│  🔍 빠른 검색     │                                          │
│    cloud service │  ─────────────────────────────────────── │
│    penetration   │  [질문 입력창]                           │
│                  │                                          │
└──────────────────┴──────────────────────────────────────────┘
```

### 3.2 FDA 결함 분석

**방법 1: 사이드바 버튼 클릭**
1. 좌측 사이드바에서 카테고리 펼치기 (예: Software/Cybersecurity)
2. 원하는 결함 버튼 클릭 (예: SC-11: Penetration Testing)
3. 자동으로 분석 시작

**방법 2: 직접 입력**
```
SC-11 관련 우리 문서 현황 분석해줘
```

### 3.3 일관성 체크

**예시 질문:**
```
클라우드 서비스 관련 내용 전체 문서에서 찾아서 일관성 체크해줘
```

**시스템 응답 예시:**
```
## 현재 문서 현황
- Security Risk Management Plan: "Configuration of the Cloud Platform" 언급
- Product Security Whitepaper: "cloud environment" 언급
- eSTAR: "전자 인터페이스 없음" 기재

## 갭 분석
❌ 모순 발견:
- 일부 문서: 클라우드 사용
- eSTAR: 전자 인터페이스 없음
```

### 3.4 컨텍스트 유지 대화

이전 대화 내용을 기억하므로 연속 질문 가능:

```
User: SC-11 분석해줘
Assistant: [SC-11 분석 결과]

User: 그러면 이거 해결하려면 어떻게 해야해?
Assistant: [이전 SC-11 맥락을 유지하며 해결 방안 제시]

User: MCRA Bob이 말한 Security Architecture Views는 우리 문서에 있어?
Assistant: [검색 후 있는지 없는지 답변]
```

### 3.5 대화 초기화
- 하단의 "🗑️ 대화 초기화" 버튼 클릭
- 새로운 주제로 시작할 때 사용

---

## 4. CLI 사용법

### 4.1 기본 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `fda-rag search` | 문서 검색 | `fda-rag search "cloud penetration"` |
| `fda-rag ask` | 질문 (Claude 분석) | `fda-rag ask "SC-11 분석해줘"` |
| `fda-rag analyze` | 결함 분석 | `fda-rag analyze SC-11` |
| `fda-rag consistency` | 일관성 체크 | `fda-rag consistency cloud` |
| `fda-rag cloud` | 클라우드 관련 전체 검색 | `fda-rag cloud` |
| `fda-rag interactive` | 대화형 모드 | `fda-rag interactive` |
| `fda-rag stats` | 인덱싱 통계 | `fda-rag stats` |

### 4.2 검색 예시

```bash
# 기본 검색
fda-rag search "penetration testing cloud"

# 카테고리 필터
fda-rag search "risk analysis" --category cybersecurity

# FINAL 문서만 검색
fda-rag search "lead II" --final-only

# 결과 개수 지정
fda-rag search "sampling rate" --k 20
```

### 4.3 대화형 모드

```bash
fda-rag interactive
```

```
>>> SC-11 분석해줘
[분석 결과 출력]

>>> search: cloud deployment
[검색 결과만 출력]

>>> consistency: electronic interface
[일관성 체크 결과]

>>> quit
```

---

## 5. FDA 결함 목록 (21개)

### 5.1 Device Description (DD) - 4개

| ID | 항목 | 담당 |
|----|------|------|
| DD-1 | ECG Input Validation - 메타데이터/포맷 검증, 에러 코드 | AI Lead |
| DD-2 | Lead II Nomenclature - 전극 위치와 명칭 불일치 | CTO |
| DD-3 | Sampling Rate (64-512Hz) - 범위 지원 근거, 필터 설명 | AI Lead |
| DD-4 | Substantial Equivalence - 성인+소아 차이, Output 비교 | RA |

### 5.2 Labeling (LB) - 1개

| ID | 항목 | 담당 |
|----|------|------|
| LB-5 | Integration Guide - 사용자 통합 가이드 누락 | CTO |

### 5.3 Software/Cybersecurity (SC) - 9개

| ID | 항목 | 담당 |
|----|------|------|
| SC-6 | Risk Analysis - ISO 14971 불일치, Severity 불일치 등 | RA |
| SC-7 | SBOM EOS/EOL - 컴포넌트 업그레이드 일정 | CTO |
| SC-8 | CVE Remediation - 취약점 대응/정당화 | CTO |
| SC-9 | Unresolved Anomalies - CWE 고려, 보안 영향 평가 | CTO |
| SC-10 | Cybersecurity Controls - 상세 문서화 | CTO |
| SC-11 | **Penetration Testing (Cloud)** - Cloud 제외 정당화 없음 | CTO |
| SC-12 | Cybersecurity Labeling - IFU 미포함 | RA |
| SC-13 | Cybersecurity Mgmt Plan - 패치 주기 설명 없음 | CTO |
| SC-14 | Interoperability - 전자 인터페이스 미신고 | CTO |

### 5.4 Performance Testing (PT) - 6개

| ID | 항목 | 담당 |
|----|------|------|
| PT-15 | Human Factors (URRA) - Use-Related Risk Analysis 없음 | RA |
| PT-16 | EC57/IEC 60601 Reports - line-by-line report 필요 | AI Lead |
| PT-17 | ML Validation - Subgroup, US site, Race 다양성 | AI Lead |
| PT-18 | Multiple Output Validation - Confusion matrix 등 | AI Lead |
| PT-19 | Signal Quality Rejection - Rejection rate 미보고 | AI Lead |
| PT-20 | HR/HRV Statistics - Deming, Bland-Altman 필요 | AI Lead |

### 5.5 Minor (MN) - 1개

| ID | 항목 | 담당 |
|----|------|------|
| MN-1 | Prescription Statement - 21 CFR 801.109 문구 누락 | RA |

---

## 6. 활용 시나리오

### 6.1 시나리오 1: FDA 결함 대응 준비

**상황**: SC-11 (Cloud Pen Test) 대응 방안 검토

```
1. Web UI 접속
2. 사이드바 > Software/Cybersecurity > SC-11 클릭
3. 분석 결과 확인:
   - FDA 요구사항
   - 현재 문서에 있는 내용
   - 누락된 부분
   - 대응 방안
4. 후속 질문: "MCRA가 말한 Security Architecture Views 문서 있어?"
```

### 6.2 시나리오 2: 문서 일관성 검토

**상황**: eSTAR 제출 전 클라우드 관련 내용 일관성 확인

```
User: 우리 문서에서 클라우드/웹서버/전자 인터페이스 관련 내용 전부 찾아서 일관성 체크해줘

[시스템이 전체 문서 검색 후 불일치 부분 식별]

User: eSTAR에 뭐라고 적혀있어?

User: Product Security Whitepaper에는?

User: 이 두 개가 충돌하는데 어떻게 수정해야 해?
```

### 6.3 시나리오 3: 컨설턴트 조언 확인

**상황**: MCRA Bob이 조언한 내용이 우리 문서에 반영되어 있는지 확인

```
User: Security Architecture Views 관련 내용 우리 문서에 있어?

User: Threat Modelling 문서에서 cloud boundary 정의되어 있어?

User: API만 테스트해도 된다는 근거가 있어?
```

---

## 7. 주의사항

### 7.1 시스템 한계

| 한계 | 설명 |
|------|------|
| **최종 판단은 사람** | AI 분석은 참고용, 규제 결정은 전문가가 |
| **새 문서 반영** | 새 문서 추가 시 재인덱싱 필요 (`fda-rag index --force`) |
| **할루시네이션 가능** | 반드시 참조 문서 직접 확인 |

### 7.2 재인덱싱이 필요한 경우

- 새 문서 추가/수정 시
- 문서 폴더 구조 변경 시

```bash
fda-rag index --force
```

### 7.3 API 키 관리

`.env` 파일에 API 키 저장됨 - **절대 Git에 커밋하지 말 것**

---

## 8. 문제 해결

### 8.1 "관련 문서를 찾을 수 없습니다"

- 검색어를 다르게 시도
- 영어/한글 혼용해서 검색
- 더 구체적인 키워드 사용

### 8.2 Web UI 접속 안됨

```bash
# 기존 프로세스 종료
pkill -f streamlit

# 재시작
source venv/bin/activate
streamlit run app.py --server.port 8510
```

### 8.3 응답이 느림

- 문서 검색: 1-2초
- Claude 분석: 10-30초 (정상)

---

## 9. 연락처

| 담당 | 역할 |
|------|------|
| CTO (Rick) | 기술 문서, Cybersecurity |
| AI Lead (Ian) | 알고리즘, Performance Testing |
| RA | 규제 문서, Labeling |

---

## 부록 A: 빠른 참조 카드

```
┌─────────────────────────────────────────────────────────┐
│  FDA RAG 빠른 참조                                      │
├─────────────────────────────────────────────────────────┤
│  Web UI: http://localhost:8510                         │
│                                                         │
│  자주 쓰는 질문:                                        │
│  • "SC-11 분석해줘"                                    │
│  • "클라우드 관련 일관성 체크해줘"                      │
│  • "Lead II 관련 내용 어디있어?"                        │
│  • "이 결함 해결하려면 어떻게 해야해?"                  │
│                                                         │
│  CLI:                                                   │
│  • fda-rag analyze SC-11                               │
│  • fda-rag consistency cloud                           │
│  • fda-rag interactive                                 │
└─────────────────────────────────────────────────────────┘
```
