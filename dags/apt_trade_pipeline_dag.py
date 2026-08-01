import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# 1. src 모듈 임포트를 위한 경로 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.append(SRC_PATH)

from fetch_api import fetch_apt_trade_batch
from load_to_duckdb import upsert_to_duckdb
from transform_views import create_analytics_views

# 2. DAG 기본 설정
default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# 3. Task 함수 정의 (Airflow PythonOperator 용)
def task_extract_api(**context):
    """[Step 1] API 수집 - 전월 및 현재월 데이터 수집"""
    # 현재 날짜 기준 연월 산출 (예: 202608)
    now = datetime.now()
    start_ymd = (now - timedelta(days=30)).strftime("%Y%m")
    end_ymd = now.strftime("%Y%m")
    
    target_lawd_codes = ["11110", "11140", "11170"] # 종로구, 중구, 용산구
    
    print(f"🚀 API 데이터 수집 시작 ({start_ymd} ~ {end_ymd})")
    raw_df = fetch_apt_trade_batch(
        lawd_cd_list=target_lawd_codes,
        start_ymd=start_ymd,
        end_ymd=end_ymd
    )
    
    # XCom을 통해 다음 Task로 DataFrame 전달
    return raw_df.to_json()

def task_load_duckdb(**context):
    """[Step 2] DuckDB 적재 및 멱등성 보장"""
    import pandas as pd
    
    # 이전 Task에서 수집한 raw_df 가져오기
    ti = context["ti"]
    raw_df_json = ti.xcom_pull(task_ids="extract_api_task")
    
    if not raw_df_json:
        print("⚠️ 적재할 데이터가 없습니다.")
        return

    raw_df = pd.read_json(raw_df_json)
    
    db_path = os.path.join(PROJECT_ROOT, "apt_trade.duckdb")
    upsert_to_duckdb(raw_df, db_path=db_path)

def task_transform_views(**context):
    """[Step 3] Data Mart View 갱신"""
    db_path = os.path.join(PROJECT_ROOT, "apt_trade.duckdb")
    create_analytics_views(db_path=db_path)

# 4. DAG 정의
with DAG(
    dag_id="korea_apt_trade_elt_pipeline",
    default_args=default_args,
    description="국토교통부 아파트 실거래가 수집-적재-변환 ELT 파이프라인",
    schedule_interval="0 6 1 * *",  # 매월 1일 오전 06:00 (KST) 실행
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["realestate", "duckdb", "elt"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_api_task",
        python_callable=task_extract_api,
    )

    load_task = PythonOperator(
        task_id="load_duckdb_task",
        python_callable=task_load_duckdb,
    )

    transform_task = PythonOperator(
        task_id="transform_views_task",
        python_callable=task_transform_views,
    )

    # 5. Task 실행 순서 (의존성) 연결
    extract_task >> load_task >> transform_task