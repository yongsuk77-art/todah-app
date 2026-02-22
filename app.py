import streamlit as st
import requests
import json

# ==========================================
# 1. API 키 설정 (깃허브 연동용 안전한 코드)
# ==========================================
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# --- 기존: 노션에 데이터 '쓰기' 함수 ---
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

# --- 추가: 노션에서 데이터 '읽어오기' 함수 ---
def get_from_notion():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    # 최신 작성일 기준으로 정렬해서 가져오기
    payload = {
        "sorts": [{"timestamp": "created_time", "direction": "descending"}]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# ==========================================
# 2. 어플 화면 그리기 (탭 기능 추가)
# ==========================================
st.set_page_config(page_title="토다 나눔방", page_icon="🌿")
st.title("🌿 토다 공동체 나눔방")
st.subheader("예수님을 닮아가는 우리의 매일의 기록")

# 화면을 두 개의 탭으로 나눕니다!
tab1, tab2 = st.tabs(["📝 나눔 작성하기", "📖 나눔 모아보기"])

# --- 첫 번째 탭: 글쓰기 화면 ---
with tab1:
    st.write("환영합니다! 이곳은 공동체와 함께 감사와 기도제목, 그리고 묵상을 나누는 공간입니다.")
    with st.form("share_form"):
        input_title = st.text_input("제목 (예: 오늘 하루도 지켜주심에 감사합니다)")
        input_category = st.selectbox("카테고리", ["감사 나눔", "기도제목 나눔", "말씀 묵상", "영성 도우미"])
        input_content = st.text_area("나눌 내용을 자유롭게 적어주세요", height=200)
        
        submitted = st.form_submit_button("나눔 등록하기")

    if submitted:
        if input_title == "" or input_content == "":
            st.warning("제목과 내용을 모두 입력해 주세요! 😅")
        else:
            status = send_to_notion(input_title, input_category, input_content)
            if status == 200:
                st.success(f"할렐루야! '{input_title}' 글이 등록되었습니다! 옆의 '나눔 모아보기' 탭을 눌러 확인해보세요! 🎉")
                st.balloons()
            else:
                st.error(f"오류가 발생했어요. (에러 코드: {status})")

# --- 두 번째 탭: 읽기 화면 (펼쳐보기 기능) ---
with tab2:
    st.write("지체들이 남긴 은혜로운 나눔을 확인해 보세요!")
    
    # 새로고침 버튼 (새 글이 바로 안 보일 때 누르는 용도)
    if st.button("🔄 최신 나눔 불러오기"):
        st.rerun()
    
    st.divider()

    with st.spinner("노션에서 나눔을 불러오는 중입니다... 잠시만 기다려주세요 ⏳"):
        notion_data = get_from_notion()
        results = notion_data.get("results", [])

        if not results:
            st.info("아직 등록된 나눔이 없습니다. 첫 번째 나눔의 주인공이 되어보세요!")
        else:
            # 노션에서 가져온 글들을 하나씩 꺼내서 화면에 그려줍니다
            for page in results:
                props = page["properties"]
                
                # 데이터 추출 (에러 방지를 위해 try-except 사용)
                try:
                    title = props["이름"]["title"][0]["plain_text"]
                except:
                    title = "제목 없음"
                    
                try:
                    category = props["카테고리"]["select"]["name"]
                except:
                    category = "분류 없음"
                    
                try:
                    content = props["내용"]["rich_text"][0]["plain_text"]
                except:
                    content = "내용이 없습니다."

                try:
                    # 작성 날짜 (예: 2023-10-25T08:30:00.000Z -> 2023-10-25 로 자르기)
                    date_str = page["created_time"].split("T")[0]
                except:
                    date_str = "날짜 알 수 없음"

                # 아코디언(Expander) UI: 클릭하면 내용이 펼쳐집니다!
                with st.expander(f"📅 {date_str} | [{category}] {title}"):
                    st.write(content)