import streamlit as st
import requests
import json
import datetime

# ==========================================
# 1. API 키 설정 (보안 유지)
# ==========================================
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# --- 데이터 보내기 ---
def send_to_notion(title, category, content):
    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "이름": { "title": [{"text": {"content": title}}] },
            "카테고리": { "select": {"name": category} },
            "내용": { "rich_text": [{"text": {"content": content}}] }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code

# --- 데이터 읽어오기 ---
def get_from_notion():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "sorts": [{"timestamp": "created_time", "direction": "descending"}]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# ==========================================
# 2. 어플 화면 그리기 (4개의 탭)
# ==========================================
st.set_page_config(page_title="토다 나눔방", page_icon="🌿")
st.title("🌿 토다 공동체 나눔방")
st.subheader("예수님을 닮아가는 우리의 매일의 기록")

# 4개의 탭 생성!
tab1, tab2, tab3, tab4 = st.tabs(["📖 매일 성경", "🙏 말씀과 기도", "📝 나눔 작성", "💬 나눔 모아보기"])

# --- [탭 1] 매일 성경 ---
with tab1:
    st.subheader("📖 달력을 눌러 매일 성경을 확인하세요")
    
    # 달력 위젯 (클릭하면 월간 달력이 팝업으로 예쁘게 뜹니다)
    selected_date = st.date_input("날짜 선택", datetime.date.today())
    
    st.info(f"📅 선택하신 날짜: {selected_date}")
    st.write("*(여기에 선택한 날짜의 성경 본문과 범위가 스르륵 나타나게 됩니다!)*")
    st.warning("💡 코치의 안내: 이 기능을 완성하려면 노션에 '매일 성경 일정표'를 하나 더 만들어서 연결해야 합니다. 다음 단계에서 같이 만들어 볼까요?")

# --- [탭 2] 말씀과 기도 (관리자 전용 읽기) ---
with tab2:
    st.subheader("🙏 목회자 나눔 (말씀과 기도)")
    st.write("목회자가 수시로 올리는 묵상 자료와 기도문을 읽는 공간입니다.")
    
    if st.button("🔄 최신 자료 불러오기", key="btn_admin"):
        st.rerun()
        
    st.divider()
    with st.spinner("자료를 불러오는 중입니다..."):
        notion_data = get_from_notion()
        results = notion_data.get("results", [])
        
        admin_posts = []
        for page in results:
            try: category = page["properties"]["카테고리"]["select"]["name"]
            except: category = ""
            
            # 목사님이 작성한 '말씀 묵상', '영성 도우미'만 골라내기!
            if category in ["말씀 묵상", "영성 도우미"]:
                admin_posts.append(page)
                
        if not admin_posts:
            st.info("아직 올라온 자료가 없습니다.")
        else:
            for page in admin_posts:
                try: title = page["properties"]["이름"]["title"][0]["plain_text"]
                except: title = "제목 없음"
                try: category = page["properties"]["카테고리"]["select"]["name"]
                except: category = "분류 없음"
                try: content = page["properties"]["내용"]["rich_text"][0]["plain_text"]
                except: content = "내용이 없습니다."
                try: date_str = page["created_time"].split("T")[0]
                except: date_str = "날짜 알 수 없음"

                with st.expander(f"📅 {date_str} | [{category}] {title}"):
                    st.write(content)

# --- [탭 3] 나눔 작성하기 (성도용) ---
with tab3:
    st.write("공동체와 함께 감사와 기도제목을 나누는 공간입니다.")
    with st.form("share_form"):
        input_title = st.text_input("제목 (예: 오늘 하루도 지켜주심에 감사합니다)")
        
        # 💡 일반 성도는 묵상 자료 카테고리를 아예 선택할 수 없게 뺌!
        input_category = st.selectbox("카테고리", ["감사 나눔", "기도제목 나눔"])
        input_content = st.text_area("나눌 내용을 자유롭게 적어주세요", height=200)
        
        submitted = st.form_submit_button("나눔 등록하기")

    if submitted:
        if input_title == "" or input_content == "":
            st.warning("제목과 내용을 모두 입력해 주세요! 😅")
        else:
            status = send_to_notion(input_title, input_category, input_content)
            if status == 200:
                st.success(f"할렐루야! '{input_title}' 글이 등록되었습니다! 🎉")
                st.balloons()
            else:
                st.error(f"오류가 발생했어요. (에러 코드: {status})")

# --- [탭 4] 나눔 모아보기 (성도용) ---
with tab4:
    st.write("지체들이 남긴 은혜로운 나눔을 확인해 보세요!")
    if st.button("🔄 최신 나눔 불러오기", key="btn_user"):
        st.rerun()
    st.divider()

    with st.spinner("나눔을 불러오는 중입니다..."):
        notion_data = get_from_notion()
        results = notion_data.get("results", [])

        user_posts = []
        for page in results:
            try: category = page["properties"]["카테고리"]["select"]["name"]
            except: category = ""
            
            # 성도들이 올린 '감사 나눔', '기도제목 나눔' 카테고리만 골라내기!
            if category in ["감사 나눔", "기도제목 나눔"]:
                user_posts.append(page)

        if not user_posts:
            st.info("아직 등록된 나눔이 없습니다. 첫 번째 나눔의 주인공이 되어보세요!")
        else:
            for page in user_posts:
                try: title = page["properties"]["이름"]["title"][0]["plain_text"]
                except: title = "제목 없음"
                try: category = page["properties"]["카테고리"]["select"]["name"]
                except: category = "분류 없음"
                try: content = page["properties"]["내용"]["rich_text"][0]["plain_text"]
                except: content = "내용이 없습니다."
                try: date_str = page["created_time"].split("T")[0]
                except: date_str = "날짜 알 수 없음"

                with st.expander(f"📅 {date_str} | [{category}] {title}"):
                    st.write(content)