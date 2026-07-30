import os
import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# DuckDB 파일 경로 (.env에서 로드, 기본값 설정)
DB_PATH = os.getenv("DUCKDB_PATH", "data/real_estate.db")


def init_db(con: duckdb.DuckDBPyConnection):
    """
    [테이블 초기화]
    Raw 레이어용 아파트 매매 실거래가 테이블(raw_apt_trade)이 없으면 생성합니다.
    """
    query = """
    CREATE TABLE IF NOT EXISTS raw_apt_trade (
        lawd_cd VARCHAR,            -- 법정동코드 5자리
        apt_name VARCHAR,           # 아파트명
        price BIGINT,               -- 거래금액 (만원)
        build_year INT,             -- 준공년도
        deal_year INT,              -- 계약년도
        deal_month VARCHAR(2),      -- 계약월 (2자리)
        deal_day VARCHAR(2),        -- 계약일 (2자리)
        area DOUBLE,                -- 전용면적(㎡)
        dong VARCHAR,               -- 법정동명
        floor INT,                  -- 층수
        req_gbn VARCHAR,            -- 거래유형 (중개거래/직거래)
        estate_agent_sgg_nm VARCHAR, -- 중개업소 위치
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 적재 일시
    );
    """
    con.execute(query)


def save_to_duckdb(df: pd.DataFrame, db_path: str = DB_PATH):
    """
    [Data Loader]
    수집된 DataFrame을 DuckDB에 적재합니다.
    동일 연월/지역 중복을 방지하기 위해 덮어쓰기 형태로 처리합니다.
    """
    if df.empty:
        print("⚠️ 적재할 데이터가 없습니다 (Empty DataFrame).")
        return

    # 데이터 타입 캐스팅 및 정리
    df_clean = df.copy()
    
    # 숫자형 컬럼 변환 (빈 문자열 처리 포함)
    df_clean['price'] = pd.to_numeric(df_clean['price'], errors='coerce').fillna(0).astype('int64')
    df_clean['build_year'] = pd.to_numeric(df_clean['build_year'], errors='coerce').fillna(0).astype('int32')
    df_clean['deal_year'] = pd.to_numeric(df_clean['deal_year'], errors='coerce').fillna(0).astype('int32')
    df_clean['floor'] = pd.to_numeric(df_clean['floor'], errors='coerce').fillna(0).astype('int32')
    df_clean['area'] = pd.to_numeric(df_clean['area'], errors='coerce').fillna(0.0).astype('float64')

    # DB 디렉터리 자동 생성 (data/ 폴더가 없을 경우 대비)
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    # DuckDB 연결 (파일이 없으면 자동 생성됨)
    con = duckdb.connect(db_path)

    try:
        # 1. 테이블 초기화
        init_db(con)

        # 2. 중복 방지 (현재 수집 대상 지역/연월 데이터 삭제 후 Insert)
        unique_lawd = df_clean['lawd_cd'].unique().tolist()
        unique_year = df_clean['deal_year'].unique().tolist()
        unique_month = df_clean['deal_month'].unique().tolist()

        delete_query = """
        DELETE FROM raw_apt_trade 
        WHERE lawd_cd IN SELECT * FROM df_lawd
          AND deal_year IN SELECT * FROM df_year
          AND deal_month IN SELECT * FROM df_month;
        """
        
        # Temp DataFrames for DuckDB SQL IN clause mapping
        df_lawd = pd.DataFrame({'lawd_cd': unique_lawd})
        df_year = pd.DataFrame({'deal_year': unique_year})
        df_month = pd.DataFrame({'deal_month': unique_month})

        con.execute(
            """
            DELETE FROM raw_apt_trade 
            WHERE lawd_cd IN (SELECT lawd_cd FROM df_lawd)
              AND deal_year IN (SELECT deal_year FROM df_year)
              AND deal_month IN (SELECT deal_month FROM df_month)
            """
        )

        # 3. DuckDB DataFrame Direct Insert
        con.execute(
            """
            INSERT INTO raw_apt_trade (
                lawd_cd, apt_name, price, build_year, deal_year, 
                deal_month, deal_day, area, dong, floor, req_gbn, estate_agent_sgg_nm
            )
            SELECT 
                lawd_cd, apt_name, price, build_year, deal_year, 
                deal_month, deal_day, area, dong, floor, req_gbn, estate_agent_sgg_nm
            FROM df_clean
            """
        )

        # 4. 적재 결과 확인
        total_count = con.execute("SELECT COUNT(*) FROM raw_apt_trade").fetchone()[0]
        print(f"✅ DuckDB 적재 완료! (신규/갱신: {len(df_clean)}건 | raw_apt_trade 총 누적: {total_count}건)")

    except Exception as e:
        print(f"💥 DuckDB 적재 중 오류 발생: {e}")
    finally:
        con.close()


if __name__ == "__main__":
    # fetch_api.py로부터 수집 모듈 임포트 후 연동 테스트
    from fetch_api import fetch_apt_trade_batch

    target_lawd_codes = ["11110", "11140", "11170"]
    start_month = "202511"
    end_month = "202601"

    # 1. API 수집 실행
    df_fetched = fetch_apt_trade_batch(
        lawd_cd_list=target_lawd_codes,
        start_ymd=start_month,
        end_ymd=end_month
    )

    # 2. DuckDB 적재 실행
    save_to_duckdb(df_fetched)