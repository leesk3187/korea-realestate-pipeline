import os
import duckdb
import pandas as pd
from fetch_api import fetch_apt_trade_batch

DB_PATH = "apt_trade.duckdb"

def create_table_if_not_exists(conn: duckdb.DuckDBPyConnection):
    """DuckDB 테이블 및 PK(복합키) 설정"""
    conn.execute("""
    CREATE TABLE IF NOT EXISTS apt_trade (
        lawd_cd VARCHAR,
        apt_name VARCHAR,
        price INTEGER,
        build_year INTEGER,
        deal_year INTEGER,
        deal_month VARCHAR,
        deal_day VARCHAR,
        deal_date DATE,
        area DOUBLE,
        dong VARCHAR,
        floor INTEGER,
        req_gbn VARCHAR,
        estate_agent_sgg_nm VARCHAR,
        buyer_gbn VARCHAR,
        seller_gbn VARCHAR,
        apt_seq VARCHAR,
        cno VARCHAR,
        srg_mode VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (lawd_cd, apt_name, area, floor, deal_date, price)
    );
    """)

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """API Raw 데이터의 타입을 정제 및 변환 (부족한 컬럼 자동 보완)"""
    if df.empty:
        return df

    df = df.copy()

    # 1. DB 스키마에 정의된 필수 컬럼 목록
    required_columns = [
        'lawd_cd', 'apt_name', 'price', 'build_year', 'deal_year', 
        'deal_month', 'deal_day', 'area', 'dong', 'floor', 
        'req_gbn', 'estate_agent_sgg_nm', 'buyer_gbn', 'seller_gbn', 
        'apt_seq', 'cno', 'srg_mode'
    ]

    # 2. DataFrame에 없는 컬럼은 빈 문자열("")로 자동 생성 (일반/상세 API 호환성 보장)
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""

    # 3. 숫자형 타입 변환
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0).astype(int)
    df['build_year'] = pd.to_numeric(df['build_year'], errors='coerce').fillna(0).astype(int)
    df['deal_year'] = pd.to_numeric(df['deal_year'], errors='coerce').fillna(0).astype(int)
    df['floor'] = pd.to_numeric(df['floor'], errors='coerce').fillna(0).astype(int)
    df['area'] = pd.to_numeric(df['area'], errors='coerce').fillna(0.0).astype(float)

    # 4. 날짜 컬럼 생성 (YYYY-MM-DD)
    df['deal_date'] = pd.to_datetime(
        df['deal_year'].astype(str) + '-' + 
        df['deal_month'].astype(str).str.zfill(2) + '-' + 
        df['deal_day'].astype(str).str.zfill(2),
        errors='coerce'
    ).dt.date

    return df

def upsert_to_duckdb(df: pd.DataFrame, db_path: str = DB_PATH):
    """DuckDB에 Upsert(Merge) 수행하여 데이터 적재"""
    if df.empty:
        print("⚠️ 적재할 데이터가 없습니다.")
        return

    df_clean = transform_data(df)
    
    conn = duckdb.connect(db_path)
    create_table_if_not_exists(conn)

    # 임시 등록(Staging) 후 Upsert 수행
    conn.register('df_staging', df_clean)
    
    upsert_query = """
    INSERT INTO apt_trade (
        lawd_cd, apt_name, price, build_year, deal_year, deal_month, deal_day, 
        deal_date, area, dong, floor, req_gbn, estate_agent_sgg_nm, 
        buyer_gbn, seller_gbn, apt_seq, cno, srg_mode
    )
    SELECT 
        lawd_cd, apt_name, price, build_year, deal_year, deal_month, deal_day, 
        deal_date, area, dong, floor, req_gbn, estate_agent_sgg_nm, 
        buyer_gbn, seller_gbn, apt_seq, cno, srg_mode
    FROM df_staging
    ON CONFLICT (lawd_cd, apt_name, area, floor, deal_date, price) 
    DO UPDATE SET
        req_gbn = EXCLUDED.req_gbn,
        estate_agent_sgg_nm = EXCLUDED.estate_agent_sgg_nm,
        buyer_gbn = EXCLUDED.buyer_gbn,
        seller_gbn = EXCLUDED.seller_gbn,
        cno = EXCLUDED.cno,
        srg_mode = EXCLUDED.srg_mode;
    """
    
    conn.execute(upsert_query)
    
    count = conn.execute("SELECT COUNT(*) FROM apt_trade").fetchone()[0]
    print(f"✅ DuckDB 적재 완료! (현재 총 누적 데이터: {count:,}건)")
    
    conn.close()

if __name__ == "__main__":
    target_lawd_codes = ["11110", "11140", "11170"]
    
    # fetch_api.py와 동일하게 3개 연월 범위로 수집 지정
    raw_df = fetch_apt_trade_batch(
        lawd_cd_list=target_lawd_codes,
        start_ymd="202511",  # 수집 시작 연월
        end_ymd="202601"     # 수집 종료 연월
    )
    
    # DuckDB 적재 실행
    upsert_to_duckdb(raw_df)