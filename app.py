import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="서울 아파트 실거래가 대시보드",
    page_icon="🏢",
    layout="wide"
)

DB_PATH = "apt_trade.duckdb"

@st.cache_data(ttl=300)
def load_data():
    """DuckDB View 데이터 로드 (Read-Only 모드로 동시성 확보)"""
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    df_summary = conn.execute("SELECT * FROM v_monthly_region_summary").df()
    df_top = conn.execute("SELECT * FROM v_top_ranked_apts").df()
    df_detail = conn.execute("SELECT * FROM v_apt_trade_detail").df()
    
    conn.close()
    return df_summary, df_top, df_detail

# 데이터 가져오기
df_summary, df_top, df_detail = load_data()

# 2. 대시보드 헤더
st.title("🏢 서울 주요 자치구 아파트 실거래가 대시보드")
st.markdown("국토교통부 API 데이터 기반 · **종로구 / 중구 / 용산구** 실거래 분석")
st.markdown("---")

# 3. 사이드바 - 지역구 필터링
st.sidebar.header("🔍 검색 필터")
selected_sgg = st.sidebar.multiselect(
    "지역구 선택",
    options=df_detail["sgg_nm"].unique(),
    default=df_detail["sgg_nm"].unique()
)

# 필터링 적용
filtered_summary = df_summary[df_summary["sgg_nm"].isin(selected_sgg)]
filtered_top = df_top[df_top["sgg_nm"].isin(selected_sgg)]
filtered_detail = df_detail[df_detail["sgg_nm"].isin(selected_sgg)]

# 4. 주요 KPI 메트릭 카드
st.subheader("📈 주요 요약 지표")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_trades = len(filtered_detail)
avg_price_eok = round(filtered_detail["price_eok"].mean(), 2) if total_trades > 0 else 0
avg_pyeong_price = round(filtered_detail["price_per_pyeong"].mean(), 0) if total_trades > 0 else 0
max_trade = filtered_detail.loc[filtered_detail["price_eok"].idxmax()] if total_trades > 0 else None

kpi1.metric("총 거래 건수", f"{total_trades:,} 건")
kpi2.metric("평균 거래가", f"{avg_price_eok} 억 원")
kpi3.metric("평균 평당가", f"{avg_pyeong_price:,.0f} 만원/평")
if max_trade is not None:
    kpi4.metric("최고가 거래", f"{max_trade['price_eok']} 억 원", f"{max_trade['apt_name']} ({max_trade['sgg_nm']})")

st.markdown("---")

# 5. 시각화 차트 영역 (2열 레이아웃)
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 월별/지역별 거래량 추이")
    filtered_summary["ym"] = filtered_summary["deal_year"].astype(str) + "-" + filtered_summary["deal_month"].astype(str).str.zfill(2)
    fig_count = px.bar(
        filtered_summary, 
        x="ym", 
        y="trade_count", 
        color="sgg_nm", 
        barmode="group",
        labels={"ym": "거래연월", "trade_count": "거래 건수", "sgg_nm": "지역구"},
        title="지역구별 월간 거래량 비교"
    )
    st.plotly_chart(fig_count, use_container_width=True)

with col2:
    st.subheader("💰 지역구별 평균 평당가(만원/평) 추이")
    fig_price = px.line(
        filtered_summary, 
        x="ym", 
        y="avg_price_per_pyeong", 
        color="sgg_nm", 
        markers=True,
        labels={"ym": "거래연월", "avg_price_per_pyeong": "평당가(만원)", "sgg_nm": "지역구"},
        title="지역구별 평균 평당가 동향"
    )
    st.plotly_chart(fig_price, use_container_width=True)

st.markdown("---")

# 6. 하단 데이터 테이블
tab1, tab2 = st.columns([1, 1])

with tab1:
    st.subheader("🏆 지역구별 최고가 거래 Top 10")
    st.dataframe(
        filtered_top[["sgg_nm", "apt_name", "area_pyeong", "price_eok", "deal_date"]]
        .sort_values(by="price_eok", ascending=False)
        .head(10),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.subheader("📋 실거래 상세 데이터")
    st.dataframe(
        filtered_detail[["deal_date", "sgg_nm", "dong", "apt_name", "area_pyeong", "floor", "price_eok"]]
        .sort_values(by="deal_date", ascending=False),
        use_container_width=True,
        hide_index=True
    )