import os
import time
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from typing import List
from dotenv import load_dotenv

# ==========================================
# 1. 환경 변수(.env) 로드 및 기본 설정
# ==========================================
load_dotenv()

# 공공데이터포털 서비스 인증키 (디코딩키 사용 권장)
API_KEY = os.getenv("DATA_GO_KR_API_KEY")

# 아파트 매매 실거래가 기본 API URL (.env 파일에 URL_APT_TRADE 미설정 시 기본 URL 사용)
BASE_URL = os.getenv("URL_APT_TRADE", "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade")

def fetch_apt_trade_single(lawd_cd: str, deal_ymd: str, max_retries: int = 3) -> pd.DataFrame:
    params = {
        'serviceKey': API_KEY,
        'LAWD_CD': lawd_cd,
        'DEAL_YMD': deal_ymd,
        'numOfRows': '1000',
        'pageNo': '1'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    # 💡 최대 max_retries 횟수만큼 재시도
    for attempt in range(1, max_retries + 1):
        try:
            # 타임아웃을 15초로 상향
            response = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ [HTTP Error {response.status_code}] LAWD_CD: {lawd_cd}, DEAL_YMD: {deal_ymd} (시도 {attempt}/{max_retries})")
                time.sleep(1)
                continue

            root = ET.fromstring(response.content)
            
            result_code = root.findtext('.//resultCode') or root.findtext('.//header/resultCode')
            if result_code and result_code not in ['00', '000']:
                result_msg = root.findtext('.//resultMsg') or root.findtext('.//header/resultMsg')
                print(f"⚠️ [API Error {result_code}] {result_msg} (LAWD_CD: {lawd_cd}, DEAL_YMD: {deal_ymd})")
                return pd.DataFrame()

            items = root.findall('.//item')
            data_list = []
            
            for item in items:
                row = {
                    'lawd_cd': lawd_cd,                                                         # [지역 정보] 요청 파라미터의 법정동코드 5자리 (예: '11110')
                    'apt_name': (item.findtext('aptNm') or '').strip(),                         # [아파트명] <aptNm> : 단지명 (예: '경희궁자이(2단지)')
                    'price': (item.findtext('dealAmount') or '').strip().replace(',', ''),      # [거래금액] <dealAmount> : 거래가격(만원 단위, 쉼표 제거) (예: '150000')
                    'build_year': item.findtext('buildYear', ''),                              # [건축년도] <buildYear> : 준공 연도 (예: '2017')
                    'deal_year': item.findtext('dealYear', ''),                                # [계약연도] <dealYear> : 매매 계약 체결 연도 (예: '2026')
                    'deal_month': item.findtext('dealMonth', '').zfill(2),                      # [계약월] <dealMonth> : 매매 계약 체결 월(2자리 맞춤) (예: '01')
                    'deal_day': item.findtext('dealDay', '').zfill(2),                          # [계약일] <dealDay> : 매매 계약 체결 일자(2자리 맞춤) (예: '05')
                    'area': item.findtext('excluUseAr', ''),                                    # [전용면적] <excluUseAr> : 전용면적(㎡) (예: '84.835')
                    'dong': (item.findtext('umdNm') or '').strip(),                             # [법정동명] <umdNm> : 읍/면/동 이름 (예: '홍파동')
                    'floor': item.findtext('floor', ''),                                        # [층수] <floor> : 해당 거래 건의 층수 (예: '12')
                    'req_gbn': (item.findtext('reqGbn') or '').strip(),                         # [거래유형] <reqGbn> : 중개거래 / 직거래 구분 (예: '중개거래')
                    'estate_agent_sgg_nm': (item.findtext('estateAgentSggNm') or '').strip(),   # [중개업소 소재지] <estateAgentSggNm> : 중개사 소재 시군구 (예: '서울 종로구')
                    
                    # ----------------------------------------------------
                    # [추후 상세 API(URL_APT_TRADE_DEV) 전환 시 활용할 컬럼]
                    # ----------------------------------------------------
                    # 'buyer_gbn': (item.findtext('buyerGbn') or '').strip(),                   # [매수자 구분] <buyerGbn> : 매수 주체 (예: '개인', '법인', '외국인')
                    # 'seller_gbn': (item.findtext('sllrGbn') or '').strip(),                  # [매도자 구분] <sllrGbn> : 매도 주체 (예: '개인', '법인', '외국인')
                }
                data_list.append(row)
                
            return pd.DataFrame(data_list)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"⚠️ [Timeout/Connection Error] LAWD_CD: {lawd_cd}, DEAL_YMD: {deal_ymd} (시도 {attempt}/{max_retries}) - {e}")
            time.sleep(1.5)  # 재시도 전 잠시 대기
            
        except Exception as e:
            print(f"💥 [Exception] LAWD_CD: {lawd_cd}, DEAL_YMD: {deal_ymd} - {e}")
            return pd.DataFrame()

    print(f"❌ [최종 실패] LAWD_CD: {lawd_cd}, DEAL_YMD: {deal_ymd} - {max_retries}회 재시도 실패")
    return pd.DataFrame()

def generate_ymd_range(start_ymd: str, end_ymd: str) -> List[str]:
    """
    [연월 범위 생성 함수]
    시작연월(YYYYMM)부터 종료연월(YYYYMM)까지의 월별 연월 문자열 리스트를 생성합니다.
    
    예: ("202511", "202601") -> ["202511", "202512", "202601"]
    """
    start_date = datetime.strptime(start_ymd, "%Y%m")
    end_date = datetime.strptime(end_ymd, "%Y%m")
    
    ymd_list = []
    current = start_date
    while current <= end_date:
        ymd_list.append(current.strftime("%Y%m"))
        # 12월이면 다음 해 1월로 변경, 아니면 다음 달로 변경
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
            
    return ymd_list


def fetch_apt_trade_batch(lawd_cd_list: List[str], start_ymd: str, end_ymd: str, delay_sec: float = 0.2) -> pd.DataFrame:
    """
    [일괄 수집 배치 함수]
    여러 지역(LAWD_CD)과 연월 범위(start_ymd ~ end_ymd)를 순회하며 데이터를 수집하고 합칩니다.
    
    :param lawd_cd_list: 5자리 법정동코드 문자열 리스트
    :param start_ymd: 수집 시작연월 (YYYYMM)
    :param end_ymd: 수집 종료연월 (YYYYMM)
    :param delay_sec: API 트래픽 제어를 위한 디레이 시간(초)
    :return: 전체 수집 결과가 병합된 pandas DataFrame
    """
    ymd_list = generate_ymd_range(start_ymd, end_ymd)
    total_iterations = len(lawd_cd_list) * len(ymd_list)
    print(f"🚀 총 {len(lawd_cd_list)}개 지역 × {len(ymd_list)}개 연월 = 총 {total_iterations}회 수집 시작\n")
    
    dfs = []
    count = 0
    
    # 지역 리스트 × 연월 리스트 이중 루프 순회
    for lawd_cd in lawd_cd_list:
        for deal_ymd in ymd_list:
            count += 1
            print(f"[{count}/{total_iterations}] 수집 중... (지역코드: {lawd_cd}, 조회연월: {deal_ymd})", end="\r")
            
            # 단일 수집 실행
            df_single = fetch_apt_trade_single(lawd_cd, deal_ymd)
            if not df_single.empty:
                dfs.append(df_single)
            
            # 과도한 연속 요청으로 인한 IP/API 차단을 방지하기 위해 잠시 대기
            time.sleep(delay_sec)
            
    print("\n\n✅ 모든 데이터 수집 완료!")
    
    # 수집된 여러 DataFrame을 하나의 DataFrame으로 세로 통합
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()


# ==========================================
# 3. 메인 실행부 (로컬 테스트용)
# ==========================================
if __name__ == "__main__":
    # 테스트 대상 법정동코드 5자리 (11110: 종로구, 11140: 중구, 11170: 용산구)
    target_lawd_codes = ["11110", "11140", "11170"]
    
    # 테스트 대상 연월 범위 (2025년 11월 ~ 2026년 1월)
    start_month = "202511"
    end_month = "202601"
    
    # 일괄 수집 실행
    df_result = fetch_apt_trade_batch(
        lawd_cd_list=target_lawd_codes,
        start_ymd=start_month,
        end_ymd=end_month
    )
    
    # 수집 결과 검증 출력
    print(f"\n=== 최종 수집 데이터 요약 (총 {len(df_result)}건) ===")
    if not df_result.empty:
        print(df_result.info())
        print("\n[지역별 수집 건수]")
        print(df_result['lawd_cd'].value_counts())