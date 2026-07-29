import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from dotenv import load_dotenv

# .env 파일 읽기
load_dotenv()

API_KEY = os.getenv("DATA_GO_KR_API_KEY")
URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"

def fetch_apt_trade_data(lawd_cd: str, deal_ymd: str) -> pd.DataFrame:
    """
    lawd_cd: 법정동코드 5자리 (예: 서울 종로구 11110)
    deal_ymd: 계약월 6자리 (예: 202601)
    """
    params = {
        'serviceKey': API_KEY,
        'LAWD_CD': lawd_cd,
        'DEAL_YMD': deal_ymd,
        'numOfRows': '1000',
        'pageNo': '1'
    }
    
    response = requests.get(URL, params=params)
    if response.status_code != 200:
        print(f"API 호출 실패: {response.status_code}")
        return pd.DataFrame()

    root = ET.fromstring(response.content)
    items = root.findall('.//item')
    
    data_list = []
    for item in items:
        row = {
            'apt_name': item.findtext('aptNm', '').strip(),
            'price': item.findtext('dealAmount', '').strip().replace(',', ''),
            'build_year': item.findtext('buildYear', ''),
            'deal_year': item.findtext('dealYear', ''),
            'deal_month': item.findtext('dealMonth', ''),
            'deal_day': item.findtext('dealDay', ''),
            'area': item.findtext('excluUseAr', ''),
            'dong': item.findtext('umdNm', ''),
            'jibun': item.findtext('jibun', ''),
            'floor': item.findtext('floor', '')
        }
        data_list.append(row)
        
    df = pd.DataFrame(data_list)
    return df

if __name__ == "__main__":
    # 테스트 실행 (서울 종로구 11110, 2026년 01월)
    df_result = fetch_apt_trade_data("11110", "202601")
    print(f"수집된 건수: {len(df_result)}")
    print(df_result.head())