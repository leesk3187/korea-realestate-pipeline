import sys
import os

# src 폴더 경로 추가 (모듈 임포트용)
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from fetch_api import fetch_apt_trade_batch
from load_to_duckdb import upsert_to_duckdb
from transform_views import create_analytics_views, query_analytics_summary

def run_pipeline(lawd_cd_list, start_ymd, end_ymd):
    print("=" * 60)
    print("🚀 [1/3] Step 1: 국토교통부 아파트 실거래가 API 수집 (Extract)")
    print("=" * 60)
    raw_df = fetch_apt_trade_batch(
        lawd_cd_list=lawd_cd_list,
        start_ymd=start_ymd,
        end_ymd=end_ymd
    )
    
    if raw_df.empty:
        print("⚠️ 수집된 데이터가 없습니다. 파이프라인을 종료합니다.")
        return

    print("\n" + "=" * 60)
    print("🚀 [2/3] Step 2: DuckDB 적재 및 멱등성 보장 (Load)")
    print("=" * 60)
    upsert_to_duckdb(raw_df)

    print("\n" + "=" * 60)
    print("🚀 [3/3] Step 3: 데이터 변환 및 분석용 Data Mart View 구축 (Transform)")
    print("=" * 60)
    create_analytics_views()
    
    print("\n" + "=" * 60)
    print("📊 파이프라인 최종 결과 검증")
    print("=" * 60)
    query_analytics_summary()

if __name__ == "__main__":
    # 대상: 서울 종로구(11110), 중구(11140), 용산구(11170)
    # 기간: 2025년 11월 ~ 2026년 1월
    target_lawd_codes = ["11110", "11140", "11170"]
    
    run_pipeline(
        lawd_cd_list=target_lawd_codes,
        start_ymd="202511",
        end_ymd="202601"
    )