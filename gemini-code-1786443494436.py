import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests
from datetime import datetime

# 페이지 기본 설정
st.set_page_config(
    page_title="해상 수입 화물 & 선박 실시간 트래킹",
    page_icon="🚢",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 1. 세션 상태(Session State) 초기화 - 사용자 등록 B/L 목록 저장소
# -----------------------------------------------------------------------------
if "bl_list" not in st.session_state:
    st.session_state.bl_list = [
        {
            "bl_no": "GDY0419405",
            "vessel_name": "HYUNDAI DRIVE",
            "imo": "9632783",
            "item_name": "자동차 부품 / 모터 샤프트",
            "eta": "2026-08-14",
            "lat": 34.80,
            "lon": 128.95,
            "speed": 13.5,
            "origin": "Yantian, CN",
            "destination": "Busan, KR",
            "status": "항해 중 (Underway)"
        },
        {
            "bl_no": "MSC12345678",
            "vessel_name": "MSC GULSUN",
            "imo": "9839430",
            "item_name": "알루미늄 / 원자재",
            "eta": "2026-08-18",
            "lat": 31.23,
            "lon": 121.47,
            "speed": 14.2,
            "origin": "Shanghai, CN",
            "destination": "Busan, KR",
            "status": "항해 중 (Underway)"
        }
    ]

# -----------------------------------------------------------------------------
# 2. 실시간 선박 API 호출 함수 (MarineTraffic / VesselFinder 연동 가능 구문)
# -----------------------------------------------------------------------------
def fetch_live_vessel_position(vessel_name_or_imo, api_key=None):
    """
    실제 API 키가 있을 경우 MarineTraffic / VesselFinder에서 최신 위경도를 가져오는 함수.
    API 키가 없거나 테스트 중일 때는 등록된 좌표 기반으로 작동합니다.
    """
    if api_key:
        try:
            # 예시: VesselFinder / MarineTraffic API 호출 endpoint
            url = f"https://api.vesselfinder.com/vessels?userkey={api_key}&imo={vessel_name_or_imo}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return {
                    "lat": data[0]["LAT"],
                    "lon": data[0]["LON"],
                    "speed": data[0]["SPEED"],
                    "status": data[0]["STATUS_NAME"]
                }
        except Exception as e:
            st.error(f"API 호출 중 오류 발생: {e}")
    return None

# -----------------------------------------------------------------------------
# 3. 메인 UI 구성
# -----------------------------------------------------------------------------
st.title("🚢 수입 B/L 화물 실시간 위치 추적 시스템")
st.caption("앞으로 배송 올 B/L 및 선박 정보를 등록하여 실시간으로 모니터링하세요.")

# 사이드바: 1) 신규 B/L 등록 폼
st.sidebar.header("➕ 신규 수입 B/L 등록")
with st.sidebar.form("add_bl_form", clear_on_submit=True):
    new_bl = st.text_input("B/L 번호 *", placeholder="예: GDY0419405")
    new_vessel = st.text_input("선박명 (Vessel Name) *", placeholder="예: HYUNDAI DRIVE")
    new_imo = st.text_input("IMO 번호 (선택)", placeholder="예: 9632783")
    new_item = st.text_input("수입 품목 / 비고", placeholder="예: 블로워 모터 / 샤프트")
    new_eta = st.date_input("도착 예정일 (ETA)")
    
    # 위치 대략 설정 (기본값: 동아시아 연안)
    st.markdown("---")
    st.caption("📍 초기 위치 설정 (위도/경도)")
    new_lat = st.number_input("위도 (Latitude)", value=34.8000, format="%.4f")
    new_lon = st.number_input("경도 (Longitude)", value=128.9500, format="%.4f")
    
    submitted = st.form_submit_button("B/L 등록하기", type="primary")
    
    if submitted:
        if new_bl and new_vessel:
            # 중복 체크 후 추가
            existing_bls = [item["bl_no"] for item in st.session_state.bl_list]
            if new_bl.strip().upper() in existing_bls:
                st.sidebar.error("이미 등록된 B/L 번호입니다.")
            else:
                st.session_state.bl_list.append({
                    "bl_no": new_bl.strip().upper(),
                    "vessel_name": new_vessel.strip().upper(),
                    "imo": new_imo.strip(),
                    "item_name": new_item,
                    "eta": str(new_eta),
                    "lat": new_lat,
                    "lon": new_lon,
                    "speed": 12.0,
                    "origin": "수입항",
                    "destination": "Busan, KR",
                    "status": "운항 중"
                })
                st.sidebar.success(f"B/L [{new_bl}] 등록 완료!")
                st.rerun()
        else:
            st.sidebar.error("B/L 번호와 선박명은 필수 입력입니다.")

# -----------------------------------------------------------------------------
# 4. 메인 화면: B/L 선택 및 위치 조회
# -----------------------------------------------------------------------------
if st.session_state.bl_list:
    # 등록된 B/L 목록 표
    st.subheader("📋 관리 중인 수입 B/L 목록")
    df_bl = pd.DataFrame(st.session_state.bl_list)
    
    # 보기 좋게 컬럼명 변경
    display_df = df_bl[["bl_no", "vessel_name", "item_name", "eta", "status"]].copy()
    display_df.columns = ["B/L 번호", "선박명", "수입 품목", "ETA (도착예정)", "현재 상태"]
    st.dataframe(display_df, use_container_width=True)

    st.markdown("---")

    # 추적할 B/L 선택 드롭다운
    bl_options = [f"{item['bl_no']} ({item['vessel_name']} - {item['item_name']})" for item in st.session_state.bl_list]
    selected_option = st.selectbox("🎯 실시간 위치 추적할 B/L 선택", bl_options)
    
    # 선택된 B/L 데이터 추출
    selected_bl_no = selected_option.split(" ")[0]
    target_data = next((item for item in st.session_state.bl_list if item["bl_no"] == selected_bl_no), None)

    if target_data:
        # 상단 요약 카드
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("B/L 번호", target_data["bl_no"])
        c2.metric("선박명", target_data["vessel_name"])
        c3.metric("품목", target_data["item_name"])
        c4.metric("도착 예정일 (ETA)", target_data["eta"])

        # 지도 및 상세 레이아웃
        m_col, i_col = st.columns([2.5, 1])

        with m_col:
            st.subheader("📍 전체 수입 B/L 실시간 해상 위치")
            
            # 지도 중심: 선택한 배 위치 기준
            m = folium.Map(
                location=[target_data["lat"], target_data["lon"]],
                zoom_start=6,
                tiles="OpenStreetMap"
            )
            
            # 💡 등록된 모든 B/L을 지도에 마커로 표시
            for item in st.session_state.bl_list:
                # 선택된 B/L은 '빨간색', 나머지는 '파란색' 마커로 구분
                is_selected = (item["bl_no"] == selected_bl_no)
                marker_color = "red" if is_selected else "blue"
                
                popup_html = f"""
                <div style="font-family: sans-serif; width: 180px;">
                    <h4>{item['vessel_name']}</h4>
                    <b>B/L:</b> {item['bl_no']}<br>
                    <b>품목:</b> {item['item_name']}<br>
                    <b>ETA:</b> {item['eta']}<br>
                    <b>속도:</b> {item['speed']} kts
                </div>
                """
                
                folium.Marker(
                    location=[item["lat"], item["lon"]],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{'🔴 [선택됨] ' if is_selected else '🔵 '}{item['vessel_name']} ({item['bl_no']})",
                    icon=folium.Icon(color=marker_color, icon="ship", prefix="fa")
                ).add_to(m)

            st_folium(m, width="100%", height=500)
            
            # 마커 추가
            popup_html = f"""
            <div style="font-family: sans-serif; width: 180px;">
                <h4>{target_data['vessel_name']}</h4>
                <b>B/L:</b> {target_data['bl_no']}<br>
                <b>품목:</b> {target_data['item_name']}<br>
                <b>ETA:</b> {target_data['eta']}<br>
                <b>속도:</b> {target_data['speed']} kts
            </div>
            """
            folium.Marker(
                location=[target_data["lat"], target_data["lon"]],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{target_data['vessel_name']} ({target_data['bl_no']})",
                icon=folium.Icon(color="red", icon="ship", prefix="fa")
            ).add_to(m)

            st_folium(m, width="100%", height=500)

        with i_col:
            st.subheader("⚙️ 관리 및 세부 정보")
            st.write(f"**IMO 번호:** {target_data['imo'] if target_data['imo'] else '미입력'}")
            st.write(f"**현재 위도:** `{target_data['lat']}`")
            st.write(f"**현재 경도:** `{target_data['lon']}`")
            st.write(f"**운항 속력:** `{target_data['speed']} knots`")
            st.write(f"**목적지:** {target_data['destination']}")

            st.markdown("---")
            # 삭제 버튼
            if st.button("🗑️ 이 B/L 삭제하기", type="secondary"):
                st.session_state.bl_list = [item for item in st.session_state.bl_list if item["bl_no"] != selected_bl_no]
                st.success("해당 B/L이 삭제되었습니다.")
                st.rerun()

else:
    st.info("현재 등록된 B/L이 없습니다. 왼쪽 사이드바에서 새 B/L을 등록해 주세요.")
    st.warning("조회 결과가 없습니다. 선박명(예: MSC GULSUN) 또는 B/L 번호(예: MSC12345678)를 확인해 주세요.")
