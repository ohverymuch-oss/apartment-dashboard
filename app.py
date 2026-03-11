import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import plotly.express as px
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ── API KEY: st.secrets 우선, 없으면 사이드바 입력 ──────────────────
def get_api_key():
    try:
        return st.secrets["API_KEY"]
    except Exception:
        return ""

# ── 지역 코드 (시/도 → 시/군/구) ────────────────────────────────────
REGION_CODES = {
    "서울특별시": {
        "강남구": "11680", "강동구": "11740", "강북구": "11305", "강서구": "11500",
        "관악구": "11620", "광진구": "11215", "구로구": "11530", "금천구": "11545",
        "노원구": "11350", "도봉구": "11320", "동대문구": "11230", "동작구": "11590",
        "마포구": "11440", "서대문구": "11410", "서초구": "11650", "성동구": "11200",
        "성북구": "11290", "송파구": "11710", "양천구": "11470", "영등포구": "11560",
        "용산구": "11170", "은평구": "11380", "종로구": "11110", "중구": "11140",
        "중랑구": "11260",
    },
    "경기도": {
        "수원시 장안구": "41111", "수원시 권선구": "41113", "수원시 팔달구": "41115", "수원시 영통구": "41117",
        "성남시 수정구": "41131", "성남시 중원구": "41133", "성남시 분당구": "41135",
        "의정부시": "41150", "안양시 만안구": "41171", "안양시 동안구": "41173",
        "부천시": "41190", "광명시": "41210", "평택시": "41220", "동두천시": "41250",
        "안산시 상록구": "41271", "안산시 단원구": "41273", "고양시 덕양구": "41281",
        "고양시 일산동구": "41285", "고양시 일산서구": "41287", "과천시": "41290",
        "구리시": "41310", "남양주시": "41360", "오산시": "41370", "시흥시": "41390",
        "군포시": "41410", "의왕시": "41430", "하남시": "41450", "용인시 처인구": "41461",
        "용인시 기흥구": "41463", "용인시 수지구": "41465", "파주시": "41480",
        "이천시": "41500", "안성시": "41550", "김포시": "41570", "화성시": "41590",
        "광주시": "41610", "양주시": "41630", "포천시": "41650", "여주시": "41670",
    },
    "인천광역시": {
        "중구": "28110", "동구": "28140", "미추홀구": "28177", "연수구": "28185",
        "남동구": "28200", "부평구": "28237", "계양구": "28245", "서구": "28260",
        "강화군": "28710", "옹진군": "28720",
    },
    "부산광역시": {
        "중구": "26110", "서구": "26140", "동구": "26170", "영도구": "26200",
        "부산진구": "26230", "동래구": "26260", "남구": "26290", "북구": "26320",
        "해운대구": "26350", "사하구": "26380", "금정구": "26410", "강서구": "26440",
        "연제구": "26470", "수영구": "26500", "사상구": "26530", "기장군": "26710",
    },
    "대구광역시": {
        "중구": "27110", "동구": "27140", "서구": "27170", "남구": "27200",
        "북구": "27230", "수성구": "27260", "달서구": "27290", "달성군": "27710",
    },
    "대전광역시": {
        "동구": "30110", "중구": "30140", "서구": "30170", "유성구": "30200", "대덕구": "30230",
    },
    "광주광역시": {
        "동구": "29110", "서구": "29140", "남구": "29155", "북구": "29170", "광산구": "29200",
    },
    "울산광역시": {
        "중구": "31110", "남구": "31140", "동구": "31170", "북구": "31200", "울주군": "31710",
    },
    "세종특별자치시": {
        "세종시": "36110",
    },
}

# ── API 엔드포인트 (부동산 유형별) ───────────────────────────────────
API_ENDPOINTS = {
    "아파트": "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev",
    "오피스텔": "https://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade",
    "연립/다세대(빌라)": "https://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade",
}

# ── XML 태그 (유형별로 다름) ─────────────────────────────────────────
TAG_MAP = {
    "아파트":          {"name": "aptNm",    "amount": "dealAmount", "area": "excluUseAr", "dong": "umdNm", "floor": "floor",    "year": "dealYear", "month": "dealMonth", "day": "dealDay"},
    "오피스텔":        {"name": "offiNm",   "amount": "dealAmount", "area": "excluUseAr", "dong": "umdNm", "floor": "floor",    "year": "dealYear", "month": "dealMonth", "day": "dealDay"},
    "연립/다세대(빌라)": {"name": "mhouseNm","amount": "dealAmount", "area": "excluUseAr", "dong": "umdNm", "floor": "floor",    "year": "dealYear", "month": "dealMonth", "day": "dealDay"},
}

def safe_text(item, tag):
    el = item.find(tag)
    return el.text.strip() if el is not None and el.text else ""

@st.cache_data(ttl=86400)
def fetch_data(api_key, lawd_cd, deal_ymd, prop_type):
    base_url = API_ENDPOINTS[prop_type]
    tags     = TAG_MAP[prop_type]
    url = f"{base_url}?serviceKey={api_key}&LAWD_CD={lawd_cd}&DEAL_YMD={deal_ymd}&numOfRows=1000&pageNo=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/xml, text/xml, */*",
    }
    response = None
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if not response.content.strip().startswith(b"<"):
            st.error("❌ API 인증 실패. 아래 응답을 확인하세요.")
            st.code(response.text, language="text")
            return pd.DataFrame()

        root = ET.fromstring(response.content)
        rc   = root.findtext(".//resultCode", "")
        rm   = root.findtext(".//resultMsg", "")
        if rc and rc not in ("00", "0000", "000"):
            st.error(f"❌ API 오류 [{rc}]: {rm}")
            st.code(response.text, language="xml")
            return pd.DataFrame()

        rows = []
        for item in root.findall(".//item"):
            try:
                price  = int(safe_text(item, tags["amount"]).replace(",", ""))
                area   = float(safe_text(item, tags["area"]))
                name   = safe_text(item, tags["name"])
                dong   = safe_text(item, tags["dong"])
                floor  = safe_text(item, tags["floor"])
                year   = safe_text(item, tags["year"])
                month  = safe_text(item, tags["month"]).zfill(2)
                day    = safe_text(item, tags["day"]).zfill(2)
                date   = pd.to_datetime(f"{year}-{month}-{day}")
                per_py = round(price / (area * 0.3025)) if area > 0 else 0
                rows.append({
                    "거래일자":      date,
                    "매물명":        name,
                    "법정동":        dong,
                    "전용면적(㎡)":  area,
                    "층":            floor,
                    "거래금액(만원)": price,
                    "평당가(만원)":   per_py,
                })
            except Exception:
                continue

        if not rows:
            st.warning("데이터가 0건입니다.")
            st.code(response.text, language="xml")

        return pd.DataFrame(rows)

    except ET.ParseError as e:
        st.error(f"❌ XML 파싱 실패: {e}")
        if response: st.code(response.text)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ 요청 오류: {e}")
        if response: st.code(response.text)
        return pd.DataFrame()

def to_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="거래내역")
    return buf.getvalue()

# ── 페이지 설정 ──────────────────────────────────────────────────────
st.set_page_config(page_title="부동산 실거래가 대시보드", layout="wide", page_icon="🏢")
st.title("🏢 부동산 실거래가 분석 대시보드")
st.caption("데이터 출처: 국토교통부 실거래가 공개시스템 API")

# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 조회 설정")

    # API KEY
    secret_key = get_api_key()
    if secret_key:
        api_key_input = secret_key
        st.success("🔑 API Key 자동 적용됨")
    else:
        api_key_input = st.text_input(
            "🔑 API Key (인코딩키)",
            type="password",
            help="data.go.kr → 마이페이지 → 인증키 → '일반 인증키(인코딩)' 복사"
        )

    st.divider()

    # ── 지역 연쇄 선택 ───────────────────────────────────────────────
    st.subheader("📍 지역 선택")
    sido = st.selectbox("시/도", list(REGION_CODES.keys()))
    sigungu_dict = REGION_CODES[sido]
    sigungu = st.selectbox("시/군/구", list(sigungu_dict.keys()))
    lawd_cd = sigungu_dict[sigungu]

    st.divider()

    # ── 매물 설정 ────────────────────────────────────────────────────
    st.subheader("🏠 매물 설정")
    prop_type = st.selectbox("부동산 유형", list(API_ENDPOINTS.keys()))

    today = datetime.today()
    month_options = [(today - relativedelta(months=i)).strftime("%Y%m") for i in range(13)]
    selected_month = st.selectbox("조회 연도/월", month_options)

    price_range = st.slider(
        "거래금액 범위 (만원)",
        min_value=0, max_value=300000,
        value=(0, 300000), step=1000,
        format="%d만원"
    )
    area_range = st.slider(
        "전용면적 범위 (㎡)",
        min_value=0, max_value=300,
        value=(0, 300), step=5
    )

# ── KEY 확인 ─────────────────────────────────────────────────────────
if not api_key_input or not api_key_input.strip():
    st.warning("👈 사이드바에 API Key를 입력하세요.")
    st.stop()

# ── 데이터 조회 ──────────────────────────────────────────────────────
with st.spinner(f"'{sido} {sigungu}' {selected_month} 데이터 불러오는 중..."):
    df_raw = fetch_data(api_key_input.strip(), lawd_cd, selected_month, prop_type)

if df_raw.empty:
    st.warning("해당 조건의 거래 데이터가 없습니다.")
    st.stop()

# ── 필터 적용 ────────────────────────────────────────────────────────
df = df_raw[
    (df_raw["거래금액(만원)"] >= price_range[0]) &
    (df_raw["거래금액(만원)"] <= price_range[1]) &
    (df_raw["전용면적(㎡)"]  >= area_range[0]) &
    (df_raw["전용면적(㎡)"]  <= area_range[1])
].copy()

if df.empty:
    st.warning("필터 조건에 맞는 데이터가 없습니다. 슬라이더 범위를 조정해보세요.")
    st.stop()

# ── 요약 지표 ────────────────────────────────────────────────────────
avg_price = int(df["거래금액(만원)"].mean())
max_price = int(df["거래금액(만원)"].max())
avg_py    = int(df["평당가(만원)"].mean())

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 거래건수",   f"{len(df):,}건")
c2.metric("평균 거래금액", f"{avg_price:,}만원")
c3.metric("최고 거래금액", f"{max_price:,}만원")
c4.metric("평균 평당가",   f"{avg_py:,}만원")

# ── 차트 ─────────────────────────────────────────────────────────────
st.subheader("📈 일자별 평균 거래금액 추이")
df_daily = df.groupby("거래일자")["거래금액(만원)"].mean().reset_index()
fig1 = px.line(df_daily, x="거래일자", y="거래금액(만원)", markers=True,
               title=f"{sido} {sigungu} {selected_month} 일자별 평균 거래금액")
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
    st.subheader("💰 매물별 평균 거래금액 TOP 10")
    apt_avg = df.groupby("매물명")["거래금액(만원)"].mean().nlargest(10).reset_index()
    fig3 = px.bar(apt_avg, x="거래금액(만원)", y="매물명", orientation="h",
                  color="거래금액(만원)", color_continuous_scale="Reds")
    fig3.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig3, use_container_width=True)

# ── 상세 거래 내역 (포맷팅 + 엑셀 다운로드) ──────────────────────────
st.subheader("📋 상세 거래 내역")

df_display = df.sort_values(by="거래일자", ascending=False).copy()
df_display["거래일자"] = df_display["거래일자"].dt.strftime("%Y-%m-%d")
df_display["거래금액(만원)"] = df_display["거래금액(만원)"].apply(lambda x: f"{x:,}")
df_display["평당가(만원)"]   = df_display["평당가(만원)"].apply(lambda x: f"{x:,}")

st.dataframe(df_display, use_container_width=True, hide_index=True)

# 엑셀 다운로드 버튼
excel_data = to_excel(df.sort_values(by="거래일자", ascending=False))
st.download_button(
    label="📥 엑셀로 다운로드",
    data=excel_data,
    file_name=f"실거래가_{sido}_{sigungu}_{selected_month}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
