# dags/pipeline_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# 기존 모듈 임포트
from scripts.fetch_api import fetch_api_data
from scripts.load_to_duckdb import load_data_to_duckdb
from scripts.transform_views import create_transform_views

default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="duckdb_etl_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 6 * * *",  # 매일 06:00 KST 실행
    catchup=False,
) as dag:

    task_fetch = PythonOperator(
        task_id="fetch_api_data",
        python_callable=fetch_api_data,
    )

    task_load = PythonOperator(
        task_id="load_to_duckdb",
        python_callable=load_data_to_duckdb,
    )

    task_transform = PythonOperator(
        task_id="transform_views",
        python_callable=create_transform_views,
    )

    # 의존성 정의
    task_fetch >> task_load >> task_transform