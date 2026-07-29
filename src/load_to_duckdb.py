import os
import duckdb
import pandas as pd
from fetch_api import fetch_apt_trade_data

DB_PATH = "data/real_estate.db"

def save_to_duckdb(df: pd.DataFrame, table_name: str = "raw_apt_trade"):
    if df.empty:
        print("적재할 데이터가 없습니다.")
        return

    # data 디렉토리가 없으면 생성
    os.makedirs("data", exist_ok=True)
    
    # DuckDB 연결 (파일이 없으면 자동 생성됨)
    con = duckdb.connect(DB_PATH)
    
    # Pandas DataFrame을 DuckDB 테이블로 직접 적재 (Create Table if Not Exists / Append)
    con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df WHERE 1=0")
    con.execute(f"INSERT INTO {table_name} SELECT * FROM df")
    
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"[{table_name}] 총 적재 건수: {count}건")
    con.close()

if __name__ == "__main__":
    # 1. API 수집
    df_trade = fetch_apt_trade_data("11110", "202601")
    
    # 2. DuckDB 적재
    save_to_duckdb(df_trade)