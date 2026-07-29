# 🏢 Korea Real Estate & Auction Data Pipeline (`korea-realestate-pipeline`)

> **국토교통부 부동산 실거래가 및 온비드 경공매 데이터를 활용한 End-to-End 데이터 파이프라인**  
> Apache Airflow, DuckDB, dbt, Docker 기반으로 구축된 로컬 데이터 레이크하우스(Data Lakehouse) 프로젝트입니다.

---

## 📌 Project Overview
본 프로젝트는 공공데이터포털(국토교통부, 행정안전부, 한국자산관리공사 온비드)에서 제공하는 부동산 및 경공매 데이터를 자동 수집하여, 분석에 용이한 형태의 데이터 마트(Data Mart)로 변환/적재하는 파이프라인을 구축합니다.

- **주요 목적:** 아파트/빌라 실거래가 추이 분석, 전세 갭(Gap) 분석, 온비드 공매 감정가 대비 실거래가 비교 지표 산출
- **엔지니어링 어필 포인트:**
  - **Zero-Cost Local Architecture:** 서버 비용 없이 Docker 및 DuckDB 기반으로 대용량 OLAP 연산 처리
  - **Idempotent Data Ingestion:** API 호출 및 적재 시 중복 적재를 방지하는 정등성(Idempotency) 보장
  - **Data Transformation with dbt:** Raw Data(Bronze) → Refined Data(Silver) → Data Mart(Gold) 단계별 데이터 모델링

---

## 🛠️ Tech Stack & Architecture

### Tech Stack
| 구분 | 기술 스택 |
| :--- | :--- |
| **Language** | Python 3.12 |
| **Orchestration** | Apache Airflow (Docker) |
| **Storage / DW** | DuckDB (Local File-based OLAP Engine) |
| **Transformation** | dbt (dbt-duckdb) |
| **Version Control** | Git / GitHub (Private Repo Dev -> Public) |

---

## 📂 Directory Structure

```text
korea-realestate-pipeline/
├── .gitignore             # Git 제외 설정 (.env, venv, data/ 등)
├── .env                   # API Key 및 인증 정보 (Git 미포함)
├── README.md              # 프로젝트 메인 문서
├── requirements.txt       # Python 패키지 의존성 목록
├── docker-compose.yml     # Airflow & Local DB 구동 컨테이너 설정
├── dags/                  # Airflow DAG 파이프라인
│   └── real_estate_dag.py
├── src/                   # 데이터 수집 및 적재 파이썬 스크립트
│   ├── fetch_api.py       # 공공데이터 API 수집 및 XML/JSON 파싱
│   └── load_to_duckdb.py  # DuckDB 테이블 적재
└── data/                  # Local Raw/Parquet/DuckDB 저장소 (Git 미포함)
```
## 🚀 Local Development Setup Guide
### 1. Repository Clone & Environment Setup

# 1) 저장소 클론
git clone [https://github.com/](https://github.com/)<your-username>/korea-realestate-pipeline.git
cd korea-realestate-pipeline

### 2. Environment Variables Setup (.env)
프로젝트 루트 경로에 .env 파일을 생성을 하고 공공데이터포털에서 발급받은 디코딩(Decoding) API 키를 입력합니다.
# 2) 파이썬 가상환경 생성 및 활성화 (Windows PowerShell 기준)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3) 필수 패키지 일괄 설치
pip install -r requirements.txt

# .env (Git에 올라가지 않음)
DATA_GO_KR_API_KEY="본인의_디코딩_서비스_인증키"
DUCKDB_PATH="data/real_estate.db"


### 🐳 Running with Docker Airflow
# 1) Docker 컨테이너 실행 (Airflow + Postgres)
docker-compose up -d

# 2) Airflow Web UI 접속
# http://localhost:8080 접속 후 DAG 상태 확인