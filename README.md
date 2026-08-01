# 🏢 Korea Real Estate & Auction Data Pipeline

> **국토교통부 부동산 실거래가 및 온비드 경공매 데이터를 활용한 End-to-End 데이터 파이프라인**
> Apache Airflow, DuckDB, dbt, Docker 기반으로 구축된 로컬 데이터 레이크하우스(Data Lakehouse) 프로젝트입니다.

---

## 📌 Project Overview

본 프로젝트는 공공데이터포털(국토교통부, 행정안전부, 한국자산관리공사 온비드)에서 제공하는 부동산 및 경공매 데이터를 자동 수집하여, 분석에 용이한 형태의 데이터 마트(Data Mart)로 변환/적재하는 파이프라인을 구축합니다.

**주요 목적**

- 아파트/빌라 실거래가 추이 분석
- 전세 갭(Gap) 분석
- 온비드 공매 감정가 대비 실거래가 비교 지표 산출

**엔지니어링 어필 포인트**

- **Zero-Cost Local Architecture** : 서버 비용 없이 Docker 및 DuckDB 기반으로 대용량 OLAP 연산 처리
- **Idempotent Data Ingestion** : API 호출 및 적재 시 중복 적재를 방지하는 멱등성(Idempotency) 보장
- **Data Transformation with dbt** : Raw Data(Bronze) → Refined Data(Silver) → Data Mart(Gold) 단계별 데이터 모델링

---

## 🛠️ Tech Stack & Architecture

| 구분 | 기술 스택 |
| :--- | :--- |
| **Language** | Python 3.12 |
| **Orchestration** | Apache Airflow (Docker) |
| **Storage / DW** | DuckDB (Local File-based OLAP Engine) |
| **Transformation** | dbt (dbt-duckdb) |
| **Version Control** | Git / GitHub (Private Repo Dev → Public) |

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
│   └── apt_trade_pipeline_dag.py # 아파트 실거래가 수집-적재-변환 DAG
├── src/                         # 데이터 수집, 적재, 변환 파이썬 스크립트
├   ├── fetch_api.py             # 공공데이터 API 수집 및 XML/JSON 파싱
├   ├── load_to_duckdb.py        # DuckDB raw 적재 및 Upsert
├   └── transform_views.py       # 데이터 변환 및 분석용 Data Mart View 생성
└── data/                  # Local Raw/Parquet/DuckDB 저장소 (Git 미포함)
```

---

## 🚀 Local Development Setup Guide

### 1. Repository Clone & Environment Setup

저장소를 클론하고 프로젝트 디렉토리로 이동합니다.

```bash
git clone https://github.com/your-username/korea-realestate-pipeline.git
cd korea-realestate-pipeline
```

파이썬 가상환경을 생성하고 활성화합니다. (Windows PowerShell 기준)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

필수 패키지를 일괄 설치합니다.

```bash
pip install -r requirements.txt
```

### 2. Environment Variables Setup (.env)

프로젝트 루트 경로에 `.env` 파일을 생성하고, 공공데이터포털에서 발급받은 **디코딩(Decoding) API 키**를 입력합니다.


### 3. Pipeline Execution (ELT Step)

통합 파이프라인(main.py)을 구동하여 API 수집부터 DuckDB 적재 및 Data Mart View 생성까지 한 번에 실행합니다.

```bash
python main.py
```

### 4. Streamlit Dashboard Run
적재 및 변환 완료된 데이터를 기반으로 시각화 대시보드를 실행합니다.
```bash
streamlit run app.py
```
브라우저가 열리며 http://localhost:8501에서 대시보드를 확인하실 수 있습니다.

```env
DATA_GO_KR_API_KEY="본인의_디코딩_서비스_인증키"
DUCKDB_PATH="data/real_estate.db"
```

---

## 🐳 Running with Docker Airflow

Docker 컨테이너를 실행합니다. (Airflow + Postgres)

```bash
docker-compose up -d
```

Airflow Web UI에 접속하여 DAG 상태를 확인합니다.

```text
http://localhost:8080
```