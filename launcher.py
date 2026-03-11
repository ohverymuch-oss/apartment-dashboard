# -*- coding: utf-8 -*-
import subprocess, sys, os, io

# Windows UTF-8 output fix
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

APP_CODE = r'''
import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

DEFAULT_API_KEY = "ecf9a6cf2dabead1885a711185e726c32d298060e4a4f181afe0b8a1fd42b7c7"
# 수정된 정확한 엔드포인트
BASE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"

SEOUL_LAWD_CD = {
    "강남구": "11680", "서초구": "11650", "송파구": "11710", "용산구": "11170",
    "성동구": "11200", "마포구": "11440", "노원구": "11350", "종로구": "11110",
    "강동구": "11740", "강서구": "11500", "관악구": "11620", "광진구": "11215",
    "구로구": "11530", "금천구": "11545", "도봉구": "11320", "동대문구": "11230",
    "동작구": "11590", "서대문구": "11410", "성북구": "11290", "양천구": "11470",
    "영등포구": "11560", "은평구": "11380", "중구": "11140", "중랑구": "11260",
    "강북구": "11305",
}

def safe_text(item, tag):
    el = item.find(tag)
    return el.text.strip() if el is not None and el.text else ""

@st.cache_data(ttl=86400)
def get_real_estate_data(api_key, lawd_cd, deal_ymd):
    # ✅ 1. URL 전체를 f-string으로 직접 조립 (params= 절대 사용 안 함)
    # ✅ 2. api_key 는 포털에서 복사한 인코딩키 원본 그대로 사용 (unquote/quote 없음)
    url = f"{BASE_URL}?serviceKey={api_key}&LAWD_CD={lawd_cd}&DEAL_YMD={deal_ymd}&numOfRows=1000&pageNo=1"

    # ✅ 3. 브라우저와 동일한 User-Agent 헤더 추가
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/xml, text/xml, */*",
    }

    response = None
    try:
        response = requests.get(url, headers=headers, timeout=15)

        # ✅ 4. 실패 시 response.text 전체 출력으로 디버깅
        if not response.content.strip().startswith(b"<"):
            st.error("❌ API 응답이 XML이 아닙니다. 아래 전체 응답을 확인하세요.")
            st.code(response.text, language="text")
            return pd.DataFrame()

        root = ET.fromstring(response.content)

        # OpenAPI 공통 오류 코드 확인
        result_code = root.findtext(".//resultCode", "")
        result_msg  = root.findtext(".//resultMsg", "")
        if result_code and result_code not in ("00", "0000", "000"):
            st.error(f"❌ API 오류 [{result_code}]: {result_msg}")
            st.code(response.text, language="xml")   # 전체 XML 출력
            return pd.DataFrame()

        # 실제 확인된 XML 태그로 파싱
        data_list = []
        for item in root.findall(".//item"):
            try:
                price        = int(safe_text(item, "dealAmount").replace(",", ""))
                area         = float(safe_text(item, "excluUseAr"))
                floor        = safe_text(item, "floor")
                apt          = safe_text(item, "aptNm")
                dong         = safe_text(item, "umdNm")
                year         = safe_text(item, "dealYear")
                month        = safe_text(item, "dealMonth").zfill(2)
                day          = safe_text(item, "dealDay").zfill(2)
                date         = pd.to_datetime(f"{year}-{month}-{day}")
                price_per_py = round(price / (area * 0.3025)) if area > 0 else 0
                data_list.append({
                    "거래일자":      date,
                    "아파트명":      apt,
                    "법정동":        dong,
                    "전용면적(㎡)":  area,
                    "층":            floor,
                    "거래금액(만원)": price,
                    "평당가(만원)":   price_per_py,
                })
            except Exception:
                continue

        if not data_list:
            st.warning("데이터가 0건입니다. 아래 원본 응답을 확인하세요.")
            st.code(response.text, language="xml")

        return pd.DataFrame(data_list)

    except ET.ParseError as e:
        st.error(f"❌ XML 파싱 실패: {e}")
        if response:
            st.code(response.text, language="text")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ 요청 오류: {e}")
        if response:
            st.code(response.text, language="text")
        return pd.DataFrame()

st.set_page_config(page_title="서울 아파트 실거래가", layout="wide", page_icon="🏢")
st.title("🏢 서울시 아파트 실거래가 분석 대시보드")
st.caption("데이터 출처: 국토교통부 아파트 매매 실거래가 상세자료 API")

with st.sidebar:
    st.header("🔍 조회 설정")
    api_key_input = st.text_input(
        "🔑 API Key (인코딩키)",
        value=DEFAULT_API_KEY,
        type="password",
        help="data.go.kr → 마이페이지 → 인증키 → '일반 인증키(인코딩)' 복사"
    )
    selected_gu = st.selectbox("자치구 선택", list(SEOUL_LAWD_CD.keys()))
    today = datetime.today()
    month_options = [(today - relativedelta(months=i)).strftime("%Y%m") for i in range(13)]
    selected_month = st.selectbox("조회 연도/월 (YYYYMM)", month_options)
    st.divider()
    st.info("오류 시 → data.go.kr\n마이페이지 → 인증키\n'일반 인증키(인코딩)' 복사 후 입력")

if not api_key_input.strip():
    st.warning("👈 사이드바에 API Key를 입력하세요.")
    st.stop()

lawd_cd = SEOUL_LAWD_CD[selected_gu]
with st.spinner(f"'{selected_gu}' {selected_month} 데이터 불러오는 중..."):
    df = get_real_estate_data(api_key_input.strip(), lawd_cd, selected_month)

if not df.empty:
    avg_price = int(df["거래금액(만원)"].mean())
    max_price = int(df["거래금액(만원)"].max())
    avg_py    = int(df["평당가(만원)"].mean())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 거래건수",   f"{len(df):,}건")
    c2.metric("평균 거래금액", f"{avg_price:,}만원")
    c3.metric("최고 거래금액", f"{max_price:,}만원")
    c4.metric("평균 평당가",   f"{avg_py:,}만원")

    st.subheader("📈 일자별 평균 거래금액 추이")
    df_daily = df.groupby("거래일자")["거래금액(만원)"].mean().reset_index()
    fig1 = px.line(df_daily, x="거래일자", y="거래금액(만원)", markers=True,
                   title=f"{selected_gu} {selected_month} 일자별 평균 거래금액")
    fig1.update_traces(line_color="#2563eb", marker_color="#ef4444")
    policies = [
        {"date": "2024-01-10", "name": "1.10 주택공급 확대방안"},
        {"date": "2024-08-08", "name": "8.8 공급 확대방안"},
        {"date": "2025-01-15", "name": "특례보금자리론 개편"},
    ]
    for p in policies:
        pd_ = pd.to_datetime(p["date"])
        if not df_daily.empty and df_daily["거래일자"].min() <= pd_ <= df_daily["거래일자"].max():
            fig1.add_vline(x=pd_, line_dash="dash", line_color="red",
                           annotation_text=p["name"], annotation_position="top right")
    st.plotly_chart(fig1, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🏘️ 법정동별 거래 건수")
        dong_cnt = df["법정동"].value_counts().reset_index()
        dong_cnt.columns = ["법정동", "거래건수"]
        fig2 = px.bar(dong_cnt, x="법정동", y="거래건수", color="거래건수",
                      color_continuous_scale="Blues")
        st.plotly_chart(fig2, use_container_width=True)
    with col_b:
        st.subheader("💰 아파트별 평균 거래금액 TOP 10")
        apt_avg = df.groupby("아파트명")["거래금액(만원)"].mean().nlargest(10).reset_index()
        fig3 = px.bar(apt_avg, x="거래금액(만원)", y="아파트명", orientation="h",
                      color="거래금액(만원)", color_continuous_scale="Reds")
        fig3.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📋 상세 거래 내역 보기"):
        st.dataframe(df.sort_values(by="거래일자", ascending=False), use_container_width=True)
else:
    st.warning("해당 조건의 거래 데이터가 없습니다. 다른 월을 선택해 보세요.")
'''

def run():
    print("\n" + "="*48)
    print("  Seoul Apartment Dashboard - Setup & Run")
    print("="*48)

    pkgs = ["streamlit", "pandas", "requests", "plotly", "python-dateutil"]
    print("\n[1/3] Installing packages...")
    for pkg in pkgs:
        print(f"  -> {pkg} ...", end=" ", flush=True)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print("done")

    print("\n[2/3] Creating app.py ...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_dir, "app.py")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(APP_CODE)
    print("  -> app.py created")

    print("\n[3/3] Starting dashboard ...")
    print("\n  Opening browser >> http://localhost:8501")
    print("  To stop: press Ctrl+C in this window\n")
    print("="*48 + "\n")

    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])

if __name__ == "__main__":
    run()
