import streamlit as st
import requests
import json
import datetime

# ==========================================
# 1. API 키 설정 (보안 유지 + 매일 성경 ID 추가!)
# ==========================================
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
BIBLE_DB_ID = st.secrets["BIBLE_DB_ID"] # 💡 새로 추가된 매일 성경 표 ID!

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# --- 데이터 보내기 (나눔방) ---
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

# --- 데이터 읽어오기 (나눔방) ---
def get_from_notion():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"sorts": [{"timestamp": "created_time", "direction": "descending"}]}
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# --- 데이터 읽어오기 (매일 성경 전용!) ---
def get_bible_schedule(target_date):
    url = f"https://api.notion.com/v1/databases/{BIBLE_DB_ID}/query"
    # 선택한 날짜와 똑같은 데이터만 쏙 골라오라는 마법의 필터!
    payload = {
        "filter": {
            "property": "날짜",
            "date": {"equals": str(target_date)}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


# ==========================================
# 2. 어플 화면 그리기 (4개의 탭)
# ==========================================
st.set_page_config(page_title="토다 나눔방", page_icon="🌿")
st.title("🌿 토다 공동체 나눔방")
st.subheader("예수님을 닮아가는 우리의 매일의 기록")

tab1, tab2, tab3, tab4 = st.tabs(["📖 매일 성경", "🙏 말씀과 기도", "📝 나눔 작성", "💬 나눔 모아보기"])

# --- [탭 1] 매일 성경 ---
with tab1:
    st.subheader("📖 달력을 눌러 매일 성경을 확인하세요")
    
    # 예쁜 달력 띄우기 (기본값은 오늘 날짜)
    selected_date = st.date_input("날짜 선택", datetime.date.today())
    st.divider()
    
    with st.spinner("해당 날짜의 본문을 노션에서 찾는 중입니다..."):
        bible_data = get_bible_schedule(selected_date)
        results = bible_data.get("results", [])
        
        if not results:
            st.info(f"📅 {selected_date} : 아직 등록된 매일 성경 일정이 없습니다.")
        else:
            for page in results:
                # 노션에서 데이터 뽑아오기
                try: title = page["properties"]["이름"]["title"][0]["plain_text"]
                except: title = "제목 없음"
                try: verses = page["properties"]["본문"]["rich_text"][0]["plain_text"]
                except: verses = "본문 없음"
                
                # 화면에 예쁘게 띄우기
                st.success(f"**오늘의 주제:** {title}")
                st.write(f"📖 **읽을 본문:** {verses}")

# --- [탭 2] 말씀과 기도 (관리자 전용 읽기) ---
with tab2:
    st.subheader("🙏 목회자 나눔 (말씀과 기도)")
    st.write("목회자가 수시로 올리는 묵상 자료와 기도문을 읽는 공간입니다.")
    if st.button("🔄 최신 자료 불러오기", key="btn_admin"): st.rerun()
    st.divider()
    
    with st.spinner("자료를 불러오는 중입니다..."):
        notion_data = get_from_notion()
        admin_posts = [p for p in notion_data.get("results", []) if p["properties"].get("카테고리", {}).get("select", {}).get("name") in ["말씀 묵상", "영성 도우미"]]
                
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
        user_posts = [p for p in notion_data.get("results", []) if p["properties"].get("카테고리", {}).get("select", {}).get("name") in ["묵상나눔", "감사나눔", "기도제목 나눔", "모두 나눔"]]

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