import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests

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
            "destination": "Busan, KR",
            "status": "항해 중 (Underway)"
        },
        {
            "bl_no": "SH26E0507017",
            "vessel_name": "ONE INFINITY / 009E",
            "imo": "9988776",
            "item_name": "부품 원자재",
            "eta": "2026-08-12",
            "lat": 35.10,
            "lon": 129.04,
            "speed": 11.0,
            "destination": "Busan, KR",
            "status": "운항 중"
        }
    ]

# -----------------------------------------------------------------------------
# 2. 메인 UI 구성
# -----------------------------------------------------------------------------
st.title("🚢 수입 B/L 화물 실시간 위치 추적 시스템")
st.caption("목록에서 원하는 B/L 행을 클릭하면 해당 선박의 위치로 지도가 즉시 이동합니다.")

# 사이드바: 신규 B/L 등록 폼
st.sidebar.header("➕ 신규 수입 B/L 등록")
with st.sidebar.form("add_bl_form", clear_on_submit=True):
    new_bl = st.text_input("B/L 번호 *", placeholder="예: GDY0419405")
    new_vessel = st.text_input("선박명 (Vessel Name) *", placeholder="예: HYUNDAI DRIVE")
    new_imo = st.text_input("IMO 번호 (선택)", placeholder="예: 9632783")
    new_item = st.text_input("수입 품목 / 비고", placeholder="예: 블로워 모터 / 샤프트")
    new_eta = st.date_input("도착 예정일 (ETA)")
    
    st.markdown("---")
    st.caption("📍 초기 위치 설정 (위도/경도)")
    new_lat = st.number_input("위도 (Latitude)", value=34.8000, format="%.4f")
    new_lon = st.number_input("경도 (Longitude)", value=128.9500, format="%.4f")
    
    submitted = st.form_submit_button("B/L 등록하기", type="primary")
    
    if submitted:
        if new_bl and new_vessel:
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
                    "destination": "Busan, KR",
                    "status": "운항 중"
                })
                st.sidebar.success(f"B/L [{new_bl}] 등록 완료!")
                st.rerun()
        else:
            st.sidebar.error("B/L 번호와 선박명은 필수 입력입니다.")

# -----------------------------------------------------------------------------
# 3. 메인 화면: 클릭 선택형 B/L 목록 표 & 실시간 지도
# -----------------------------------------------------------------------------
if st.session_state.bl_list:
    st.subheader("📋 관리 중인 수입 B/L 목록 (행을 클릭하여 위치 이동)")
    
    # 데이터프레임 생성
    df_bl = pd.DataFrame(st.session_state.bl_list)
    display_df = df_bl[["bl_no", "vessel_name", "item_name", "eta", "status"]].copy()
    display_df.columns = ["B/L 번호", "선박명", "수입 품목", "ETA (도착예정)", "현재 상태"]

    # 💡 [핵심] 표에서 행 클릭 시 이벤트 발생 (on_select="rerun")
    event = st.dataframe(
        display_df,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="bl_table"
    )

    # 표에서 클릭한 행 감지
    selected_rows = event.selection.get("rows", [])
    
    if selected_rows:
        selected_idx = selected_rows[0]
        target_data = st.session_state.bl_list[selected_idx]
    else:
        # 클릭한 게 없으면 첫 번째 B/L을 기본값으로 설정
        target_data = st.session_state.bl_list[0]

    selected_bl_no = target_data["bl_no"]

    st.markdown("---")

    # 상단 요약 카드
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("선택된 B/L", target_data["bl_no"])
    c2.metric("선박명", target_data["vessel_name"])
    c3.metric("품목", target_data["item_name"])
    c4.metric("도착 예정일 (ETA)", target_data["eta"])

    # 지도 및 세부 정보
    m_col, i_col = st.columns([2.5, 1])

    with m_col:
        st.subheader(f"📍 전체 B/L 위치 (현재 선택: 🔴 {target_data['vessel_name']})")
        
        # 지도 중심을 선택된 배 위치로 설정
        m = folium.Map(
            location=[target_data["lat"], target_data["lon"]],
            zoom_start=6,
            tiles="OpenStreetMap"
        )
        
        # 등록된 모든 B/L 표시 (선택된 건은 빨간색, 나머지는 파란색)
        for item in st.session_state.bl_list:
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

        st_folium(m, width="100%", height=500, key=f"map_{selected_bl_no}")

    with i_col:
        st.subheader("⚙️ 선택된 B/L 상세 정보")
        st.write(f"**IMO 번호:** {target_data['imo'] if target_data['imo'] else '미입력'}")
        st.write(f"**현재 위도:** `{target_data['lat']}`")
        st.write(f"**현재 경도:** `{target_data['lon']}`")
        st.write(f"**운항 속력:** `{target_data['speed']} knots`")
        st.write(f"**목적지:** {target_data['destination']}")

        st.markdown("---")
        if st.button("🗑️ 이 B/L 삭제하기", type="secondary"):
            st.session_state.bl_list = [item for item in st.session_state.bl_list if item["bl_no"] != selected_bl_no]
            st.success("해당 B/L이 삭제되었습니다.")
            st.rerun()

else:
    st.info("현재 등록된 B/L이 없습니다. 왼쪽 사이드바에서 새 B/L을 등록해 주세요.")
