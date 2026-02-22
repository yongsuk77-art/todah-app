import streamlit as st
import requests
import json

# ==========================================
# 1. 노션 마스터키와 ID 입력칸 (아까처럼 꼭 넣어주세요!)
# ==========================================
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 노션으로 데이터를 보내는 함수(기능)
def send_to_notion(title, category, content):
    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "이름": {
                "title": [{"text": {"content": title}}]
            },
            "카테고리": {
                "select": {"name": category}
            },
            "내용": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code

# ==========================================
# 2. 어플리케이션 화면 그리기
# ==========================================
st.set_page_config(page_title="토다 나눔방", page_icon="🌿")
st.title("🌿 토다 공동체 나눔방")
st.subheader("예수님을 닮아가는 우리의 매일의 기록")

st.write("환영합니다! 이곳은 공동체와 함께 감사와 기도제목, 그리고 묵상을 나누는 공간입니다.")
st.divider() # 가로줄 긋기

# 사용자 입력 창 만들기
with st.form("share_form"):
    input_title = st.text_input("제목 (예: 오늘 하루도 지켜주심에 감사합니다)")
    input_category = st.selectbox("카테고리", ["감사 나눔", "기도제목 나눔", "말씀 묵상", "영성 도우미"])
    input_content = st.text_area("나눌 내용을 자유롭게 적어주세요", height=200)
    
    # 글쓰기 버튼
    submitted = st.form_submit_button("나눔 등록하기")

# ==========================================
# 3. 버튼을 눌렀을 때 작동할 마법!
# ==========================================
if submitted:
    if input_title == "" or input_content == "":
        st.warning("제목과 내용을 모두 입력해 주세요! 😅")
    else:
        # 노션으로 전송!
        status = send_to_notion(input_title, input_category, input_content)
        
        if status == 200:
            st.success(f"할렐루야! '{input_title}' 글이 노션에 성공적으로 등록되었습니다! 🎉")
            st.balloons() # 축하 풍선 효과 띄우기
        else:
            st.error(f"앗, 뭔가 오류가 발생했어요. (에러 코드: {status})")