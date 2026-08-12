import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime

# 페이지 기본 설정
st.set_page_config(
    page_title="실시간 해상 수입 화물 & 선박 트래킹",
    page_icon="🚢",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 1. 샘플 데이터 / API 연동 함수 (추후 실제 API 연동 로직으로 교체)
# -----------------------------------------------------------------------------
def get_vessel_data(search_type, query):
    """
    입력받은 B/L 번호 또는 선박명/IMO로 선박 상태 및 위경도 정보를 반환하는 함수
    """
    # [가상 데이터 예시] 실제 연동 시 MarineTraffic, VesselFinder 등 외부 API 호출
    mock_db = {
        "MSC GULSUN": {
            "bl_no": "MSC12345678",
            "vessel_name": "MSC GULSUN",
            "imo": "9839430",
            "lat": 34.75,       # 위도
            "lon": 128.90,      # 경도
            "speed": 14.2,      # 속도 (knots)
            "heading": 45,      # 침로 (도)
            "origin": "Shanghai, CN",
            "destination": "Busan, KR",
            "eta": "2026-08-12 18:00 KST",
            "status": "Underway using Engine"
        },
        "EVER GIVEN": {
            "bl_no": "EGLV98765432",
            "vessel_name": "EVER GIVEN",
            "imo": "9811000",
            "lat": 22.31,
            "lon": 114.16,
            "speed": 0.2,
            "heading": 120,
            "origin": "Rotterdam, NL",
            "destination": "Hong Kong, HK",
            "eta": "2026-08-15 09:30 KST",
            "status": "Moored"
        }
    }
    
    query_upper = query.strip().upper()
    
    # B/L 번호 검색 처리
    if search_type == "B/L 번호":
        for data in mock_db.values():
            if data["bl_no"] == query_upper:
                return data
    # 선박명/IMO 검색 처리
    else:
        for name, data in mock_db.items():
            if query_upper in name or query_upper == data["imo"]:
                return data
                
    return None

# -----------------------------------------------------------------------------
# 2. UI 레이아웃 구성
# -----------------------------------------------------------------------------
st.title("🚢 실시간 해상 수입 화물 & 선박 트래킹 시스템")
st.caption("선박명, IMO 번호 또는 B/L 번호를 입력하여 현재 선박 위치와 항해 상태를 확인하세요.")

# 사이드바: 검색 조건 입력
st.sidebar.header("🔍 화물/선박 검색")
search_type = st.sidebar.radio("검색 기준 선택", ["선박명 / IMO", "B/L 번호"])
query_input = st.sidebar.text_input("검색어 입력", value="MSC GULSUN" if search_type == "선박명 / IMO" else "MSC12345678")

search_button = st.sidebar.button("조회하기", type="primary")

# 데이터 조회
vessel_info = get_vessel_data(search_type, query_input)

if vessel_info:
    # 상단 요약 정보 카드리스트
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("선박명", vessel_info["vessel_name"])
    col2.metric("B/L 번호", vessel_info["bl_no"])
    col3.metric("현재 속력", f"{vessel_info['speed']} knots")
    col4.metric("도착 예정 시간 (ETA)", vessel_info["eta"])

    st.markdown("---")

    # 대시보드 메인 영역 (지도 + 상세정보)
    map_col, info_col = st.columns([2.5, 1])

    with map_col:
        st.subheader("📍 실시간 선박 위치 (Live Map)")
        
        # Folium 지도 생성 (선박 위치 중심)
        m = folium.Map(
            location=[vessel_info["lat"], vessel_info["lon"]],
            zoom_start=7,
            tiles="OpenStreetMap"
        )
        
        # 선박 위치 마커 추가
        popup_text = f"""
        <b>{vessel_info['vessel_name']}</b><br>
        B/L: {vessel_info['bl_no']}<br>
        속도: {vessel_info['speed']} kts<br>
        목적지: {vessel_info['destination']}
        """
        
        folium.Marker(
            location=[vessel_info["lat"], vessel_info["lon"]],
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=vessel_info["vessel_name"],
            icon=folium.Icon(color="blue", icon="ship", prefix="fa")
        ).add_to(m)

        # 지도 출력
        st_folium(m, width="100%", height=500)

    with info_col:
        st.subheader("📋 항해 상세 정보")
        st.write(f"**IMO 번호:** {vessel_info['imo']}")
        st.write(f"**출발지:** {vessel_info['origin']}")
        st.write(f"**목적지:** {vessel_info['destination']}")
        st.write(f"**운항 상태:** {vessel_info['status']}")
        st.write(f"**현재 위도:** `{vessel_info['lat']}`")
        st.write(f"**현재 경도:** `{vessel_info['lon']}`")
        st.write(f"**진행 방향:** {vessel_info['heading']}°")
        
        st.info("💡 실제 운용 시 MarineTraffic / VesselFinder API와 연동하면 위도/경도가 실시간으로 자동 갱신됩니다.")

else:
    st.warning("조회 결과가 없습니다. 선박명(예: MSC GULSUN) 또는 B/L 번호(예: MSC12345678)를 확인해 주세요.")