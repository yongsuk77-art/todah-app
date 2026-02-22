import streamlit as st
import requests
import json
import datetime

# ==========================================
# 1. API 키 설정 (4개의 열쇠 모두 장착!)
# ==========================================
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]     # 성도 나눔방
BIBLE_DB_ID = st.secrets["BIBLE_DB_ID"]     # 매일 성경
PASTOR_DB_ID = st.secrets["PASTOR_DB_ID"]   # 말씀과 기도 (목회자 전용)

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# --- 데이터 보내기 (성도 나눔방) ---
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

# --- 데이터 읽어오기 (성도 나눔방) ---
def get_from_notion():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"sorts": [{"timestamp": "created_time", "direction": "descending"}]}
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# --- 데이터 읽어오기 (매일 성경) ---
def get_bible_schedule(target_date):
    url = f"https://api.notion.com/v1/databases/{BIBLE_DB_ID}/query"
    payload = {
        "filter": {
            "property": "날짜",
            "date": {"equals": str(target_date)}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# --- 데이터 읽어오기 (말씀과 기도 전용!) ---
def get_pastor_data():
    url = f"https://api.notion.com/v1/databases/{PASTOR_DB_ID}/query"
    payload = {"sorts": [{"timestamp": "created_time", "direction": "descending"}]}
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


# ==========================================
# 2. 어플 화면 그리기 (4개의 탭)
# ==========================================
st.set_page_config(page_title="토다 나눔방", page_icon="🌿")
# 기존 타이틀을 지우고 이 코드를 넣습니다! (새로고침 마법)
st.markdown(
    """
    <a href="/" target="_self" style="text-decoration: none; color: inherit;">
        <h1 style="margin-bottom: 0px; cursor: pointer;">🌿 토다 공동체 나눔방</h1>
    </a>
    """, 
    unsafe_allow_html=True
)
st.subheader("예수님을 닮아가는 우리의 매일의 기록")

tab1, tab2, tab3, tab4 = st.tabs(["📖 매일 성경", "🙏 말씀과 기도", "📝 나눔 작성", "💬 나눔 모아보기"])

# --- [탭 1] 매일 성경 ---
with tab1:
    st.subheader("📖 달력을 눌러 매일 성경을 확인하세요")
    selected_date = st.date_input("날짜 선택", datetime.date.today())
    st.divider()
    
    with st.spinner("해당 날짜의 본문을 찾는 중입니다..."):
        bible_data = get_bible_schedule(selected_date)
        results = bible_data.get("results", [])
        
        if not results:
            st.info(f"📅 {selected_date} : 아직 등록된 매일 성경 일정이 없습니다.")
        else:
            for page in results:
                try: title = page["properties"]["이름"]["title"][0]["plain_text"]
                except: title = "제목 없음"
                try: verses = page["properties"]["본문"]["rich_text"][0]["plain_text"]
                except: verses = "본문 없음"
                
                st.success(f"**오늘의 주제:** {title}")
                st.write(f"📖 **읽을 본문:** {verses}")

# --- [탭 2] 말씀과 기도 (관리자 전용 읽기) ---
with tab2:
    st.subheader("🙏 목회자 나눔 (말씀과 기도)")
    st.write("목회자가 수시로 올리는 묵상 자료와 기도문을 읽는 공간입니다.")
    if st.button("🔄 최신 자료 불러오기", key="btn_admin"): st.rerun()
    st.divider()
    
    with st.spinner("자료를 불러오는 중입니다..."):
        pastor_data = get_pastor_data()
        results = pastor_data.get("results", [])
                
        if not results:
            st.info("아직 올라온 자료가 없습니다.")
        else:
            for page in results:
                # 💡 노션 표의 '말씀과 기도' 기둥에서 제목 가져오기
                try: title = page["properties"]["말씀과 기도"]["title"][0]["plain_text"]
                except: title = "제목 없음"
                
                # 💡 내용 가져오기
                try: content = page["properties"]["내용"]["rich_text"][0]["plain_text"]
                except: content = "내용이 없습니다."
                
                # 💡 '날짜' 기둥에서 날짜 가져오기 (비어있으면 자동 생성일로 대체)
                try: date_str = page["properties"]["날짜"]["date"]["start"]
                except: date_str = page["created_time"].split("T")[0]

                # 카테고리 없이 깔끔하게 제목과 날짜만 띄우기
                with st.expander(f"📅 {date_str} | {title}"):
                    st.write(content)

# --- [탭 3] 나눔 작성하기 (성도용) ---
with tab3:
    st.write("공동체와 함께 감사와 기도제목을 나누는 공간입니다.")
    with st.form("share_form"):
        input_title = st.text_input("제목 (예: 오늘 하루도 지켜주심에 감사합니다)")
        input_category = st.selectbox("카테고리", ["묵상나눔", "감사나눔", "기도제목 나눔", "모두 나눔"])
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
    if st.button("🔄 최신 나눔 불러오기", key="btn_user"): st.rerun()
    st.divider()

    with st.spinner("나눔을 불러오는 중입니다..."):
        notion_data = get_from_notion()
        results = notion_data.get("results", [])
        
        user_posts = []
        for p in results:
            try: cat = p["properties"]["카테고리"]["select"]["name"]
            except (KeyError, TypeError): cat = ""
            
            if cat in ["묵상나눔", "감사나눔", "기도제목 나눔", "모두 나눔"]:
                user_posts.append(p)

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