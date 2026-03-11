import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ════════════════════════════════════════════════════
#  🔐 비밀번호 게이트
# ════════════════════════════════════════════════════
def check_password():
    if st.session_state.get("authenticated"):
        return True

    # ── 전체 배경 + Glassmorphism 카드 CSS ──────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700;900&display=swap');

    /* 기본 여백 제거 */
    #root > div:first-child { padding: 0; }
    [data-testid="stAppViewContainer"] > div:first-child { padding: 0; }
    [data-testid="stHeader"]  { display: none; }
    [data-testid="stToolbar"] { display: none; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* 전체 화면 배경 */
    [data-testid="stAppViewContainer"] {
        background:
            linear-gradient(rgba(5, 10, 25, 0.62), rgba(5, 10, 25, 0.62)),
            url('https://images.unsplash.com/photo-1517598798260-d55fb51f8bea?w=1800&q=85')
            center/cover no-repeat fixed;
        font-family: 'Noto Sans KR', 'Segoe UI', sans-serif;
        min-height: 100vh;
    }

    /* 중앙 정렬 래퍼 */
    .glass-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 24px;
    }

    /* Glassmorphism 카드 */
    .glass-card {
        background: rgba(255, 255, 255, 0.13);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.28);
        border-radius: 24px;
        box-shadow:
            0 8px 32px rgba(0, 0, 0, 0.45),
            inset 0 1px 0 rgba(255,255,255,0.25);
        padding: 52px 48px 40px;
        width: 100%;
        max-width: 420px;
        text-align: center;
    }

    /* 아이콘 뱃지 */
    .glass-icon {
        width: 72px; height: 72px;
        background: linear-gradient(135deg, #1e3a6e 0%, #3182ce 100%);
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 34px;
        margin-bottom: 20px;
        box-shadow: 0 6px 20px rgba(49,130,206,0.5);
    }

    .glass-card h1 {
        color: #ffffff;
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0 0 6px 0;
        line-height: 1.3;
    }
    .glass-card .slogan {
        color: rgba(255,255,255,0.62);
        font-size: 13px;
        margin: 0 0 32px 0;
        line-height: 1.6;
    }
    .glass-card .pw-label {
        display: block;
        text-align: left;
        color: rgba(255,255,255,0.80);
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    /* 입력창 */
    div[data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.12) !important;
        border: 1.5px solid rgba(255,255,255,0.3) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 15px !important;
        padding: 14px 16px !important;
        caret-color: #90cdf4;
    }
    div[data-testid="stTextInput"] input::placeholder { color: rgba(255,255,255,0.38) !important; }
    div[data-testid="stTextInput"] input:focus {
        border-color: #63b3ed !important;
        background: rgba(255,255,255,0.18) !important;
        box-shadow: 0 0 0 3px rgba(99,179,237,0.25) !important;
    }
    /* 비밀번호 눈 아이콘 */
    div[data-testid="stTextInput"] button { color: rgba(255,255,255,0.6) !important; }

    /* 접속 버튼 */
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #1e3a6e 0%, #3182ce 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        padding: 14px !important;
        letter-spacing: 0.4px !important;
        box-shadow: 0 6px 20px rgba(49,130,206,0.5) !important;
        transition: transform 0.15s, box-shadow 0.15s !important;
        margin-top: 4px;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 28px rgba(49,130,206,0.6) !important;
    }

    /* 개발자 크레딧 */
    .dev-credit {
        margin-top: 28px;
        color: rgba(255,255,255,0.38);
        font-size: 12px;
        line-height: 1.8;
        text-align: center;
    }
    .dev-credit .dev-name {
        color: rgba(255,255,255,0.75);
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 0.3px;
    }
    .dev-credit .dev-tag {
        display: inline-block;
        background: rgba(99,179,237,0.22);
        border: 1px solid rgba(99,179,237,0.4);
        color: #90cdf4;
        font-size: 10px;
        letter-spacing: 1.2px;
        padding: 2px 10px;
        border-radius: 100px;
        margin-bottom: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── 카드 상단 HTML ──────────────────────────────────────────────
    st.markdown("""
    <div class="glass-wrapper">
        <div class="glass-card">
            <div class="glass-icon">🏢</div>
            <h1>부동산 매매/전월세<br>실거래가 조회사이트</h1>
            <p class="slogan">
                데이터로 읽는 대한민국 부동산<br>
                국토교통부 실거래가 기반 분석 대시보드
            </p>
            <span class="pw-label">🔒 &nbsp;ACCESS PASSWORD</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Streamlit 위젯 (CSS 카드 위에 오버레이) ─────────────────────
    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        pw = st.text_input(
            "", type="password", key="pw_input",
            placeholder="비밀번호를 입력하세요",
            label_visibility="collapsed"
        )
        if st.button("대시보드 접속 →", use_container_width=True):
            if pw == "7601":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")

        st.markdown("""
        <div class="dev-credit">
            <div class="dev-tag">DEVELOPER</div><br>
            <span class="dev-name">KANG, SEONGIL</span><br>
            © 2026 부동산 실거래가 대시보드
        </div>
        """, unsafe_allow_html=True)

    return False

if not check_password():
    st.stop()

# ════════════════════════════════════════════════════
#  🔑 유형별 API KEY
# ════════════════════════════════════════════════════
API_KEY = "ecf9a6cf2dabead1885a711185e726c32d298060e4a4f181afe0b8a1fd42b7c7"

# ════════════════════════════════════════════════════
#  🌐 거래유형 × 부동산유형별 API 설정
#
#  [매매] dealAmount = 거래금액
#  [전월세] deposit = 보증금, monthlyRent = 월세
#
#  단독/다가구 공통 특이사항:
#    - 건물명 없음 → 법정동+지번 조합
#    - 전용면적 없음 → 연면적(totalFloorAr)
#    - 층 없음 → "-"
# ════════════════════════════════════════════════════
TRADE_CONFIG = {
    "매매": {
        "아파트": {
            "url":  "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev",
            "tags": {"name":"aptNm",       "area":"excluUseAr", "dong":"umdNm", "floor":"floor",
                     "year":"dealYear",    "month":"dealMonth", "day":"dealDay",
                     "amount":"dealAmount"},
        },
        "오피스텔": {
            "url":  "https://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade",
            "tags": {"name":"offiNm",      "area":"excluUseAr", "dong":"umdNm", "floor":"floor",
                     "year":"dealYear",    "month":"dealMonth", "day":"dealDay",
                     "amount":"dealAmount"},
        },
        "연립/다세대": {
            "url":  "https://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade",
            "tags": {"name":"mhouseNm",    "area":"excluUseAr", "dong":"umdNm", "floor":"floor",
                     "year":"dealYear",    "month":"dealMonth", "day":"dealDay",
                     "amount":"dealAmount"},
        },
        "단독/다가구": {
            "url":  "https://apis.data.go.kr/1613000/RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade",
            "tags": {"name":"jibun",       "area":"totalFloorAr","dong":"umdNm", "floor":"_none_",
                     "year":"dealYear",    "month":"dealMonth", "day":"dealDay",
                     "amount":"dealAmount"},
            "area_label": "연면적(㎡)",
        },
        "상업업무용": {
            "url":  "https://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade",
            "tags": {"name":"buildingName","area":"plottageIndex","dong":"umdNm","floor":"floor",
                     "year":"dealYear",    "month":"dealMonth", "day":"dealDay",
                     "amount":"dealAmount"},
            "area_label": "대지면적(㎡)",
        },
    },
    "전월세": {
        "아파트": {
            "url":  "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent",
            "tags": {"name":"aptNm",       "area":"excluUseAr", "dong":"umdNm", "floor":"floor",
                     "year":"dealYear",    "month":"dealMonth", "day":"dealDay",
                     "deposit":"deposit",  "monthly":"monthlyRent"},
        },
        "오피스텔": {
            "url":  "https://apis.data.go.kr/1613000/RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent",
            "tags": {"name":"offiNm",      "area":"excluUseAr", "dong":"umdNm", "floor":"floor",
                     "year":"dealYear",    "month":"dealMonth", "day":"dealDay",
                     "deposit":"deposit",  "monthly":"monthlyRent"},
        },
        "연립/다세대": {
            "url":  "https://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent",
            "tags": {"name":"mhouseNm",    "area":"excluUseAr", "dong":"umdNm", "floor":"floor",
                     "year":"dealYear",    "month":"dealMonth", "day":"dealDay",
                     "deposit":"deposit",  "monthly":"monthlyRent"},
        },
        "단독/다가구": {
            "url":  "https://apis.data.go.kr/1613000/RTMSDataSvcSHRent/getRTMSDataSvcSHRent",
            "tags": {"name":"jibun",       "area":"totalFloorAr","dong":"umdNm","floor":"_none_",
                     "year":"dealYear",    "month":"dealMonth", "day":"dealDay",
                     "deposit":"deposit",  "monthly":"monthlyRent"},
            "area_label": "연면적(㎡)",
        },
    },
}

# ════════════════════════════════════════════════════
#  📍 지역 코드 (시/도 → 시/군/구)
# ════════════════════════════════════════════════════
REGION_CODES = {
    "서울특별시": {
        "강남구":"11680","강동구":"11740","강북구":"11305","강서구":"11500",
        "관악구":"11620","광진구":"11215","구로구":"11530","금천구":"11545",
        "노원구":"11350","도봉구":"11320","동대문구":"11230","동작구":"11590",
        "마포구":"11440","서대문구":"11410","서초구":"11650","성동구":"11200",
        "성북구":"11290","송파구":"11710","양천구":"11470","영등포구":"11560",
        "용산구":"11170","은평구":"11380","종로구":"11110","중구":"11140","중랑구":"11260",
    },
    "경기도": {
        "수원시 장안구":"41111","수원시 권선구":"41113","수원시 팔달구":"41115","수원시 영통구":"41117",
        "성남시 수정구":"41131","성남시 중원구":"41133","성남시 분당구":"41135",
        "의정부시":"41150","안양시 만안구":"41171","안양시 동안구":"41173",
        "부천시":"41190","광명시":"41210","평택시":"41220","동두천시":"41250",
        "안산시 상록구":"41271","안산시 단원구":"41273","고양시 덕양구":"41281",
        "고양시 일산동구":"41285","고양시 일산서구":"41287","과천시":"41290",
        "구리시":"41310","남양주시":"41360","오산시":"41370","시흥시":"41390",
        "군포시":"41410","의왕시":"41430","하남시":"41450","용인시 처인구":"41461",
        "용인시 기흥구":"41463","용인시 수지구":"41465","파주시":"41480",
        "이천시":"41500","안성시":"41550","김포시":"41570","화성시":"41590",
        "광주시":"41610","양주시":"41630","포천시":"41650","여주시":"41670",
    },
    "인천광역시": {
        "중구":"28110","동구":"28140","미추홀구":"28177","연수구":"28185",
        "남동구":"28200","부평구":"28237","계양구":"28245","서구":"28260",
        "강화군":"28710","옹진군":"28720",
    },
    "부산광역시": {
        "중구":"26110","서구":"26140","동구":"26170","영도구":"26200",
        "부산진구":"26230","동래구":"26260","남구":"26290","북구":"26320",
        "해운대구":"26350","사하구":"26380","금정구":"26410","강서구":"26440",
        "연제구":"26470","수영구":"26500","사상구":"26530","기장군":"26710",
    },
    "대구광역시": {
        "중구":"27110","동구":"27140","서구":"27170","남구":"27200",
        "북구":"27230","수성구":"27260","달서구":"27290","달성군":"27710",
    },
    "대전광역시": {
        "동구":"30110","중구":"30140","서구":"30170","유성구":"30200","대덕구":"30230",
    },
    "광주광역시": {
        "동구":"29110","서구":"29140","남구":"29155","북구":"29170","광산구":"29200",
    },
    "울산광역시": {
        "중구":"31110","남구":"31140","동구":"31170","북구":"31200","울주군":"31710",
    },
    "세종특별자치시": {
        "세종시":"36110",
    },
}

# ════════════════════════════════════════════════════
#  🔧 유틸 함수
# ════════════════════════════════════════════════════
def safe_text(item, tag):
    if not tag or tag == "_none_":
        return ""
    el = item.find(tag)
    return el.text.strip() if el is not None and el.text else ""

def safe_float(s):
    try:
        return float(str(s).replace(",", ""))
    except Exception:
        return 0.0

def safe_int(s):
    try:
        return int(str(s).replace(",", "").strip())
    except Exception:
        return 0

def get_area_label(trade_type, prop_type):
    return TRADE_CONFIG[trade_type][prop_type].get("area_label", "전용면적(㎡)")

def is_danda(prop_type):
    return prop_type == "단독/다가구"

@st.cache_data(ttl=86400)
def fetch_data(lawd_cd, deal_ymd, trade_type, prop_type):
    """공공데이터포털 실거래가/전월세 API 단일 호출"""
    cfg  = TRADE_CONFIG[trade_type][prop_type]
    tags = cfg["tags"]
    url  = (f"{cfg['url']}"
            f"?serviceKey={API_KEY}"
            f"&LAWD_CD={lawd_cd}"
            f"&DEAL_YMD={deal_ymd}"
            f"&numOfRows=1000&pageNo=1")
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36"),
        "Accept": "application/xml, text/xml, */*",
    }
    response = None
    try:
        response = requests.get(url, headers=headers, timeout=15)

        if not response.content.strip().startswith(b"<"):
            st.error("❌ API 인증 실패 — 서버 응답:")
            st.code(response.text, language="text")
            return pd.DataFrame()

        root = ET.fromstring(response.content)
        rc   = root.findtext(".//resultCode", "")
        rm   = root.findtext(".//resultMsg", "")
        if rc and rc not in ("00", "0000", "000"):
            st.error(f"❌ API 오류 [{rc}]: {rm}")
            st.code(response.text, language="xml")
            return pd.DataFrame()

        area_label = get_area_label(trade_type, prop_type)
        rows = []

        for item in root.findall(".//item"):
            try:
                dong  = safe_text(item, tags["dong"])
                area  = safe_float(safe_text(item, tags["area"]))
                year  = safe_text(item, tags["year"])
                month = safe_text(item, tags["month"]).zfill(2)
                day   = safe_text(item, tags["day"]).zfill(2)
                date  = pd.to_datetime(f"{year}-{month}-{day}")
                floor = safe_text(item, tags["floor"]) if tags.get("floor") != "_none_" else "-"

                # 건물명: 단독/다가구는 법정동+지번
                if is_danda(prop_type):
                    jibun = safe_text(item, "jibun")
                    name  = f"{dong} {jibun}".strip() if jibun else dong
                else:
                    name = safe_text(item, tags["name"]) or "(이름없음)"

                # ── 매매 ──────────────────────────────────────
                if trade_type == "매매":
                    amount = safe_int(safe_text(item, tags["amount"]))
                    per_py = round(amount / (area * 0.3025)) if area > 0 else 0
                    rows.append({
                        "거래일자":        date,
                        "매물명":          name,
                        "법정동":          dong,
                        area_label:        area,
                        "층":              floor,
                        "거래금액(만원)":   amount,
                        "평당가(만원)":     per_py,
                    })
                # ── 전월세 ────────────────────────────────────
                else:
                    deposit = safe_int(safe_text(item, tags["deposit"]))
                    monthly = safe_int(safe_text(item, tags["monthly"]))
                    kind    = "전세" if monthly == 0 else "월세"
                    # 전세 환산 보증금 기준 평당가
                    per_py = round(deposit / (area * 0.3025)) if area > 0 else 0
                    rows.append({
                        "거래일자":        date,
                        "매물명":          name,
                        "법정동":          dong,
                        area_label:        area,
                        "층":              floor,
                        "전세/월세":        kind,
                        "보증금(만원)":     deposit,
                        "월세(만원)":       monthly,
                        "보증금 평당가":    per_py,
                    })
            except Exception:
                continue

        if not rows and response:
            st.warning("⚠️ 데이터가 0건입니다.")
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


def fetch_multiple(codes_dict, deal_ymd, trade_type, prop_type, label=""):
    """여러 지역 코드 순차 호출 후 합산"""
    frames = []
    items  = list(codes_dict.items())
    prog   = st.progress(0, text=f"{label} 데이터 수집 중...")
    for i, (name, code) in enumerate(items):
        prog.progress((i + 1) / len(items), text=f"수집 중: {name} ({i+1}/{len(items)})")
        df = fetch_data(code, deal_ymd, trade_type, prop_type)
        if not df.empty:
            frames.append(df)
    prog.empty()
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def to_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="거래내역")
    return buf.getvalue()

# ════════════════════════════════════════════════════
#  🖥️ 메인 UI
# ════════════════════════════════════════════════════
st.set_page_config(page_title="부동산 실거래가 대시보드", layout="wide", page_icon="🏢")
st.title("🏢 부동산 실거래가 분석 대시보드")
st.caption("데이터 출처: 국토교통부 실거래가 공개시스템 API")

with st.sidebar:
    st.header("🔍 조회 설정")

    # ── 지역 연쇄 선택 ───────────────────────────────
    st.subheader("📍 지역 선택")
    sido_list = ["모두"] + list(REGION_CODES.keys())
    sido      = st.selectbox("시/도", sido_list, index=sido_list.index("서울특별시"))

    if sido == "모두":
        sigungu_dict = {}
        for d in REGION_CODES.values():
            sigungu_dict.update(d)
    else:
        sigungu_dict = REGION_CODES[sido]

    sigungu_list = ["모두"] + list(sigungu_dict.keys())
    default_sigungu = sigungu_list.index("동대문구") if "동대문구" in sigungu_list else 0
    sigungu      = st.selectbox("시/군/구", sigungu_list, index=default_sigungu)

    if sido == "모두" and sigungu == "모두":
        st.warning("⚠️ 전국 조회는 수백 건의 API 호출이 발생합니다.")
    elif sigungu == "모두":
        st.info(f"💡 '{sido}' 전체 구/군을 순차 조회합니다.")

    st.divider()

    # ── 매물 설정 ────────────────────────────────────
    st.subheader("🏠 매물 설정")

    # 거래유형 체크박스 (복수 선택 가능)
    st.write("거래유형")
    cb_sale = st.checkbox("매매",   value=True,  key="cb_sale")
    cb_rent = st.checkbox("전월세", value=False, key="cb_rent")

    if not cb_sale and not cb_rent:
        st.warning("거래유형을 하나 이상 선택하세요.")
        cb_sale = True

    selected_trades = []
    if cb_sale: selected_trades.append("매매")
    if cb_rent: selected_trades.append("전월세")

    # 부동산 유형: 선택된 거래유형 모두에 존재하는 유형만 표시
    if len(selected_trades) == 1:
        prop_types = list(TRADE_CONFIG[selected_trades[0]].keys())
    else:
        rent_keys  = set(TRADE_CONFIG["전월세"].keys())
        prop_types = [p for p in TRADE_CONFIG["매매"].keys() if p in rent_keys]
    prop_type = st.selectbox("부동산 유형", prop_types)

    today          = datetime.today()
    month_options  = [(today - relativedelta(months=i)).strftime("%Y%m") for i in range(13)]
    selected_month = st.selectbox("조회 연도/월", month_options)

    if cb_sale and cb_rent:
        price_label = "거래금액/보증금 범위 (만원)"
    elif cb_rent:
        price_label = "보증금 범위 (만원)"
    else:
        price_label = "거래금액 범위 (만원)"

    price_range = st.slider(
        price_label,
        min_value=0, max_value=300000,
        value=(0, 300000), step=1000, format="%d만원"
    )
    area_range = st.slider(
        "면적 범위 (㎡)",
        min_value=0, max_value=500,
        value=(0, 500), step=5
    )

    # 전월세 포함 시 전세/월세 필터 표시
    if cb_rent:
        rent_filter = st.multiselect(
            "선택 유형",
            ["전세", "월세"],
            default=["전세", "월세"],
        )
    else:
        rent_filter = ["전세", "월세"]

    st.divider()
    if st.button("🔓 로그아웃"):
        st.session_state["authenticated"] = False
        st.rerun()

# ── 데이터 조회 (선택된 거래유형별) ────────────────────────────────
def load_df(trade_type):
    """지역/기간에 맞는 raw DataFrame 반환 (캐시 활용)"""
    if sido == "모두" and sigungu == "모두":
        all_codes = {}
        for d in REGION_CODES.values():
            all_codes.update(d)
        return fetch_multiple(all_codes, selected_month, trade_type, prop_type, f"전국({trade_type})")
    elif sigungu == "모두":
        return fetch_multiple(sigungu_dict, selected_month, trade_type, prop_type, f"{sido} 전체({trade_type})")
    else:
        lawd_cd = sigungu_dict[sigungu]
        with st.spinner(f"'{region_label}' {selected_month} {prop_type} ({trade_type}) 불러오는 중..."):
            return fetch_data(lawd_cd, selected_month, trade_type, prop_type)

if sido == "모두" and sigungu == "모두":
    region_label = "전국"
elif sigungu == "모두":
    region_label = f"{sido} 전체"
else:
    region_label = f"{sido} {sigungu}"

# ── 매매 섹션 ────────────────────────────────────────────────────
if "매매" in selected_trades:
    area_label_sale = get_area_label("매매", prop_type)
    df_raw_sale = load_df("매매")

    if df_raw_sale.empty:
        st.warning("매매: 해당 조건의 거래 데이터가 없습니다.")
    else:
        df_sale = df_raw_sale[
            (df_raw_sale["거래금액(만원)"]    >= price_range[0]) &
            (df_raw_sale["거래금액(만원)"]    <= price_range[1]) &
            (df_raw_sale[area_label_sale]     >= area_range[0])  &
            (df_raw_sale[area_label_sale]     <= area_range[1])
        ].copy()

        if df_sale.empty:
            st.warning("매매: 필터 조건에 맞는 데이터가 없습니다.")
        else:
            st.markdown("---")
            st.header("🏷️ 매매 거래 현황")

            avg_price = int(df_sale["거래금액(만원)"].mean())
            max_price = int(df_sale["거래금액(만원)"].max())
            avg_py    = int(df_sale["평당가(만원)"].mean())

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 거래건수",   f"{len(df_sale):,}건")
            c2.metric("평균 거래금액", f"{avg_price:,}만원")
            c3.metric("최고 거래금액", f"{max_price:,}만원")
            c4.metric("평균 평당가",   f"{avg_py:,}만원")

            st.subheader("📈 일자별 평균 거래금액 추이")
            df_daily = df_sale.groupby("거래일자")["거래금액(만원)"].mean().reset_index()
            fig1 = px.line(df_daily, x="거래일자", y="거래금액(만원)", markers=True,
                           title=f"{region_label} {selected_month} {prop_type} 일자별 평균 거래금액")
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
                dong_cnt = df_sale["법정동"].value_counts().reset_index()
                dong_cnt.columns = ["법정동", "거래건수"]
                fig2 = px.bar(dong_cnt, x="법정동", y="거래건수", color="거래건수",
                              color_continuous_scale="Blues")
                st.plotly_chart(fig2, use_container_width=True)
            with col_b:
                st.subheader("💰 매물별 평균 거래금액 TOP 10")
                apt_avg = df_sale.groupby("매물명")["거래금액(만원)"].mean().nlargest(10).reset_index()
                fig3 = px.bar(apt_avg, x="거래금액(만원)", y="매물명", orientation="h",
                              color="거래금액(만원)", color_continuous_scale="Reds")
                fig3.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig3, use_container_width=True)

            st.subheader("📋 상세 거래 내역")
            df_disp = df_sale.sort_values("거래일자", ascending=False).copy()
            df_disp["거래일자"]       = df_disp["거래일자"].dt.strftime("%Y-%m-%d")
            df_disp["거래금액(만원)"]  = df_disp["거래금액(만원)"].apply(lambda x: f"{x:,}")
            df_disp["평당가(만원)"]    = df_disp["평당가(만원)"].apply(lambda x: f"{x:,}")
            st.dataframe(df_disp, use_container_width=True, hide_index=True)

            excel_sale = to_excel(df_sale.sort_values("거래일자", ascending=False))
            st.download_button(
                label="📥 매매 엑셀 다운로드",
                data=excel_sale,
                file_name=f"매매_{region_label}_{selected_month}_{prop_type}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

# ── 전월세 섹션 ──────────────────────────────────────────────────
if "전월세" in selected_trades:
    area_label_rent = get_area_label("전월세", prop_type)
    df_raw_rent = load_df("전월세")

    if df_raw_rent.empty:
        st.warning("전월세: 해당 조건의 거래 데이터가 없습니다.")
    else:
        df_rent = df_raw_rent[
            (df_raw_rent["보증금(만원)"]     >= price_range[0]) &
            (df_raw_rent["보증금(만원)"]     <= price_range[1]) &
            (df_raw_rent[area_label_rent]    >= area_range[0])  &
            (df_raw_rent[area_label_rent]    <= area_range[1])  &
            (df_raw_rent["전세/월세"].isin(rent_filter))
        ].copy()

        if df_rent.empty:
            st.warning("전월세: 필터 조건에 맞는 데이터가 없습니다.")
        else:
            st.markdown("---")
            st.header("🔑 전월세 거래 현황")

            total_cnt  = len(df_rent)
            avg_dep    = int(df_rent["보증금(만원)"].mean())
            avg_mon    = int(df_rent[df_rent["전세/월세"] == "월세"]["월세(만원)"].mean())                          if (df_rent["전세/월세"] == "월세").any() else 0
            jeonse_pct = round((df_rent["전세/월세"] == "전세").sum() / total_cnt * 100, 1)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 거래건수", f"{total_cnt:,}건")
            c2.metric("평균 보증금", f"{avg_dep:,}만원")
            c3.metric("평균 월세",   f"{avg_mon:,}만원" if avg_mon > 0 else "-")
            c4.metric("전세 비율",   f"{jeonse_pct}%")

            st.subheader("📈 일자별 평균 보증금 추이")
            df_daily_rent = df_rent.groupby(["거래일자", "전세/월세"])["보증금(만원)"].mean().reset_index()
            fig1 = px.line(df_daily_rent, x="거래일자", y="보증금(만원)", color="전세/월세",
                           markers=True,
                           color_discrete_map={"전세": "#2563eb", "월세": "#f59e0b"},
                           title=f"{region_label} {selected_month} {prop_type} 일자별 평균 보증금")
            st.plotly_chart(fig1, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🥧 전세 / 월세 비율")
                pie_data = df_rent["전세/월세"].value_counts().reset_index()
                pie_data.columns = ["구분", "건수"]
                fig_pie = px.pie(pie_data, names="구분", values="건수",
                                 color="구분",
                                 color_discrete_map={"전세": "#2563eb", "월세": "#f59e0b"})
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)
            with col_b:
                st.subheader("🏘️ 법정동별 거래 건수")
                dong_cnt = df_rent["법정동"].value_counts().reset_index()
                dong_cnt.columns = ["법정동", "거래건수"]
                fig2 = px.bar(dong_cnt, x="법정동", y="거래건수", color="거래건수",
                              color_continuous_scale="Blues")
                st.plotly_chart(fig2, use_container_width=True)

            st.subheader("💰 매물별 평균 보증금 TOP 10")
            top10 = df_rent.groupby("매물명")["보증금(만원)"].mean().nlargest(10).reset_index()
            fig3  = px.bar(top10, x="보증금(만원)", y="매물명", orientation="h",
                           color="보증금(만원)", color_continuous_scale="Blues")
            fig3.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig3, use_container_width=True)

            if (df_rent["전세/월세"] == "월세").any():
                st.subheader("📊 월세 금액 분포")
                df_mol = df_rent[df_rent["전세/월세"] == "월세"]
                fig4   = px.histogram(df_mol, x="월세(만원)", nbins=30,
                                       color_discrete_sequence=["#f59e0b"],
                                       title="월세 금액 히스토그램")
                st.plotly_chart(fig4, use_container_width=True)

            st.subheader("📋 상세 거래 내역")
            df_disp = df_rent.sort_values("거래일자", ascending=False).copy()
            df_disp["거래일자"]    = df_disp["거래일자"].dt.strftime("%Y-%m-%d")
            df_disp["보증금(만원)"] = df_disp["보증금(만원)"].apply(lambda x: f"{x:,}")
            df_disp["월세(만원)"]   = df_disp["월세(만원)"].apply(lambda x: f"{x:,}")
            df_disp["보증금 평당가"] = df_disp["보증금 평당가"].apply(lambda x: f"{x:,}")
            st.dataframe(df_disp, use_container_width=True, hide_index=True)

            excel_rent = to_excel(df_rent.sort_values("거래일자", ascending=False))
            st.download_button(
                label="📥 전월세 엑셀 다운로드",
                data=excel_rent,
                file_name=f"전월세_{region_label}_{selected_month}_{prop_type}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
