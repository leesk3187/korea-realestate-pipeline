import duckdb

DB_PATH = "apt_trade.duckdb"

def create_analytics_views(db_path: str = DB_PATH):
    conn = duckdb.connect(db_path)
    
    print("🚀 DuckDB 분석용 View 및 Data Mart 생성 시작...")

    # 1. 상세 분석용 기본 View (단위 변환 및 신규 지표 계산)
    conn.execute("""
    CREATE OR REPLACE VIEW v_apt_trade_detail AS
    SELECT 
        lawd_cd,
        CASE lawd_cd
            WHEN '11110' THEN '종로구'
            WHEN '11140' THEN '중구'
            WHEN '11170' THEN '용산구'
            ELSE lawd_cd
        END AS sgg_nm,
        dong,
        apt_name,
        deal_date,
        deal_year,
        deal_month,
        price,
        ROUND(price / 10000.0, 2) AS price_eok, -- 억 단위 변환
        area,
        ROUND(area / 3.3058, 1) AS area_pyeong, -- 평수 변환
        ROUND(price / (area / 3.3058), 0) AS price_per_pyeong, -- 평당가 (만원/평)
        floor,
        build_year,
        (deal_year - build_year) AS building_age, -- 건물 연식
        req_gbn,
        estate_agent_sgg_nm
    FROM apt_trade
    WHERE price > 0 AND area > 0;
    """)
    print("  - v_apt_trade_detail 생성 완료")

    # 2. 월별 / 구별(지역별) 거래량 및 가격 동향 집계 View
    conn.execute("""
    CREATE OR REPLACE VIEW v_monthly_region_summary AS
    SELECT 
        deal_year,
        deal_month,
        sgg_nm,
        COUNT(*) AS trade_count,
        ROUND(AVG(price), 0) AS avg_price,
        ROUND(AVG(price_per_pyeong), 0) AS avg_price_per_pyeong,
        MAX(price) AS max_price,
        MIN(price) AS min_price
    FROM v_apt_trade_detail
    GROUP BY deal_year, deal_month, sgg_nm
    ORDER BY deal_year, deal_month, sgg_nm;
    """)
    print("  - v_monthly_region_summary 생성 완료")

    # 3. 단지별 최고가 거래 상위 라인업 View
    conn.execute("""
    CREATE OR REPLACE VIEW v_top_ranked_apts AS
    SELECT 
        sgg_nm,
        dong,
        apt_name,
        area_pyeong,
        price_eok,
        price_per_pyeong,
        deal_date,
        floor,
        DENSE_RANK() OVER (PARTITION BY sgg_nm ORDER BY price DESC) AS rank_in_sgg
    FROM v_apt_trade_detail;
    """)
    print("  - v_top_ranked_apts 생성 완료")

    print("✅ 모든 분석용 View가 성공적으로 구축되었습니다.\n")
    conn.close()

def query_analytics_summary(db_path: str = DB_PATH):
    """생성된 View 데이터 검증 및 분석 결과 출력"""
    conn = duckdb.connect(db_path)
    
    print("📊 [월별/지역별 거래 동향 요약]")
    df_summary = conn.execute("SELECT * FROM v_monthly_region_summary").df()
    print(df_summary.to_string(index=False))

    print("\n🏆 [지역구별 최고가 거래 아파트 Top 3]")
    df_top = conn.execute("""
        SELECT sgg_nm, apt_name, area_pyeong, price_eok, deal_date 
        FROM v_top_ranked_apts 
        WHERE rank_in_sgg <= 3
        ORDER BY sgg_nm, rank_in_sgg
    """).df()
    print(df_top.to_string(index=False))

    conn.close()

if __name__ == "__main__":
    create_analytics_views()
    query_analytics_summary()