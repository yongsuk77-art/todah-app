import streamlit as st
import requests
import json
import datetime
import time

# ==========================================
# 1. API 키 설정 (4개의 열쇠)
# ==========================================
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
BIBLE_DB_ID = st.secrets["BIBLE_DB_ID"]
PASTOR_DB_ID = st.secrets["PASTOR_DB_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# --- 데이터 통신 함수들 (이전과 동일) ---
def send_to_notion(title, category, content, date_str):
    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "이름": { "title": [{"text": {"content": title}}] },
            "카테고리": { "select": {"name": category} },
            "날짜": { "date": {"start": date_str} },
            "내용": { "rich_text": [{"text": {"content": content}}] }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code

def get_from_notion():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"sorts": [{"timestamp": "created_time", "direction": "descending"}]}
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def get_bible_schedule(target_date):
    url = f"https://api.notion.com/v1/databases/{BIBLE_DB_ID}/query"
    payload = {"filter": {"property": "날짜", "date": {"equals": str(target_date)}}}
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def get_pastor_data():
    url = f"https://api.notion.com/v1/databases/{PASTOR_DB_ID}/query"
    payload = {"sorts": [{"timestamp": "created_time", "direction": "descending"}]}
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


# ==========================================
# 2. 어플 화면 그리기 및 HTML/CSS 마법 설정
# ==========================================
st.set_page_config(page_title="토다 나눔방", page_icon="🌿", layout="wide") # 화면을 넓게 쓰기 위해 wide 추가!

# 💡 첫 화면을 예쁘게 꾸며줄 웹 디자인(CSS) 코드입니다. (무한 스크롤 애니메이션 포함)
st.markdown("""
<style>
    @keyframes scroll-up {
        0% { transform: translateY(100%); }
        100% { transform: translateY(-100%); }
    }
    .auto-scroll-box {
        overflow: hidden; position: relative; padding: 10px;
        background: white; border: 1px solid #eee; border-radius: 0 0 10px 10px;
    }
    .scroll-content {
        animation: scroll-up 20s linear infinite; display: flex; flex-direction: column; gap: 15px;
    }
    .scroll-content:hover { animation-play-state: paused; /* 마우스 올리면 멈춤! */ }
    .manual-scroll-box {
        overflow-y: auto; padding: 15px; background: white; border: 1px solid #eee; border-radius: 0 0 10px 10px;
    }
    .manual-scroll-box::-webkit-scrollbar { width: 6px; }
    .manual-scroll-box::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px;}
    .manual-scroll-box::-webkit-scrollbar-thumb { background: #ccc; border-radius: 10px; }
    
    .board-title {
        font-weight: bold; text-align: center; padding: 12px; border-radius: 10px 10px 0 0; color: #333; margin-bottom: 0;
    }
    .post-item {
        border-bottom: 1px dashed #ddd; padding-bottom: 10px; margin-bottom: 10px; font-size: 0.95em; line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)


now = int(time.time())
st.markdown(f'<a href="/?v={now}" target="_self" style="text-decoration: none; color: inherit;"><h1 style="margin-bottom: 0px; cursor: pointer;">🌿 토다 공동체 나눔방</h1></a>', unsafe_allow_html=True)
st.subheader("예수님을 닮아가는 우리의 매일의 기록")

# 💡 탭이 5개로 늘어났습니다! 첫 화면 탭이 추가되었습니다.
tab0, tab1, tab2, tab3, tab4 = st.tabs(["🏠 첫 화면", "📖 매일 성경", "🙏 말씀과 기도", "📝 나눔 작성", "💬 나눔 모아보기"])

# --- [탭 0] 🏠 기획하신 예쁜 첫 화면 (대시보드) ---
with tab0:
    st.write("오늘의 말씀과 공동체의 나눔을 한눈에 확인하세요!")
    
    # 3일치 날짜 계산하기
    today = datetime.date.today()
    three_days_ago = today - datetime.timedelta(days=3)
    
    with st.spinner("대시보드를 예쁘게 그리는 중입니다... 🎨"):
        # 1. 데이터 모두 불러오기
        bible_res = get_bible_schedule(today).get("results", [])
        pastor_res = get_pastor_data().get("results", [])
        user_res = get_from_notion().get("results", [])
        
        # 2. 데이터 분류하기
        # 2-1. 매일 성경
        bible_title = "오늘의 말씀이 없습니다."
        bible_verses = "등록된 성경 본문이 없습니다."
        if bible_res:
            try: bible_title = bible_res[0]["properties"]["이름"]["title"][0]["plain_text"]
            except: pass
            try: bible_verses = bible_res[0]["properties"]["본문"]["rich_text"][0]["plain_text"]
            except: pass
            
        # 2-2. 말씀과 기도 (최신 1개)
        pastor_title = "묵상 자료가 없습니다."
        pastor_content = ""
        if pastor_res:
            try: pastor_title = pastor_res[0]["properties"]["말씀과 기도"]["title"][0]["plain_text"]
            except: pass
            try: pastor_content = pastor_res[0]["properties"]["내용"]["rich_text"][0]["plain_text"]
            except: pass

        # 2-3. 성도 나눔 (3일치만 골라내기)
        muksang_list, gamsa_list, gido_list = "", "", ""
        for p in user_res:
            try: cat = p["properties"]["카테고리"]["select"]["name"]
            except: cat = ""
            try: date_str = p["properties"]["날짜"]["date"]["start"]
            except: date_str = p["created_time"].split("T")[0]
            
            # 날짜 비교 (3일 이내인지 확인)
            try:
                item_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if item_date < three_days_ago: continue # 3일 지났으면 패스!
            except: pass
            
            try: title = p["properties"]["이름"]["title"][0]["plain_text"]
            except: title = "제목 없음"
            try: content = p["properties"]["내용"]["rich_text"][0]["plain_text"]
            except: content = ""
            
            # 화면에 예쁘게 그릴 HTML 박스 만들기 (마우스 올리면 스크롤 멈춤 기능 포함)
            html_item = f'<div class="post-item"><b style="color:#0056b3;">[{title} | {date_str}]</b><br>{content.replace(chr(10), "<br>")}</div>'
            
            if cat == "묵상나눔": muksang_list += html_item
            elif cat == "감사나눔": gamsa_list += html_item
            elif cat == "기도제목 나눔": gido_list += html_item

        if not muksang_list: muksang_list = "<div class='post-item'>최근 3일간 올라온 묵상 나눔이 없습니다.</div>"
        if not gamsa_list: gamsa_list = "<div class='post-item'>최근 3일간 올라온 감사 나눔이 없습니다.</div>"
        if not gido_list: gido_list = "<div class='post-item'>최근 3일간 올라온 기도제목이 없습니다.</div>"

        # 3. 화면 배치 (기획하신 대로 3칸으로 나눕니다!)
        col1, col2, col3 = st.columns([1, 1.2, 1])
        
        # --- 왼쪽 칸: 오늘의 성경 본문 ---
        with col1:
            st.markdown(f'<div class="board-title" style="background-color: #ffd54f;">📖 [ 오늘의 성경 본문 ]<br>{bible_title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="auto-scroll-box" style="height: 550px;"><div class="scroll-content" style="animation-duration: 25s;">{bible_verses.replace(chr(10), "<br>")}</div></div>', unsafe_allow_html=True)
            
        # --- 가운데 칸: 목사님 묵상 & 감사/기도 ---
        with col2:
            # 위: 목회자 묵상 자료 (수동 스크롤)
            st.markdown('<div class="board-title" style="background-color: #a5d6a7;">🌿 [ 오늘의 성경 본문 묵상 자료 ]</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="manual-scroll-box" style="height: 270px; margin-bottom: 20px;"><b>[{pastor_title}]</b><br><br>{pastor_content.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            
            # 아래: 감사나눔 & 기도제목 (반반 쪼개기)
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.markdown('<div class="board-title" style="background-color: #e1bee7;">🙏 감사나눔</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="auto-scroll-box" style="height: 230px;"><div class="scroll-content" style="animation-duration: 15s;">{gamsa_list}</div></div>', unsafe_allow_html=True)
            with col2_2:
                st.markdown('<div class="board-title" style="background-color: #bbdefb;">💌 기도제목 나눔</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="auto-scroll-box" style="height: 230px;"><div class="scroll-content" style="animation-duration: 15s;">{gido_list}</div></div>', unsafe_allow_html=True)

        # --- 오른쪽 칸: 묵상 나눔 ---
        with col3:
            st.markdown('<div class="board-title" style="background-color: #ffcc80;">💬 [ 말씀 묵상 나눔 ]</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="auto-scroll-box" style="height: 550px;"><div class="scroll-content" style="animation-duration: 25s;">{muksang_list}</div></div>', unsafe_allow_html=True)

    st.divider()
    # 💡 하단에 작성 유도 메시지 추가
    st.markdown('<div style="text-align: right; font-weight: bold; font-size: 1.1em; color: #d32f2f;">나눔 기록하러 가기 👉 상단의 <span style="background-color:#ffee58; padding:3px 8px; border-radius:5px;">📝 나눔 작성</span> 탭을 클릭하세요!</div>', unsafe_allow_html=True)


# --- [탭 1] 매일 성경 ---
with tab1:
    st.subheader("📖 달력을 눌러 매일 성경을 확인하세요")
    selected_date = st.date_input("날짜 선택", datetime.date.today())
    st.divider()
    with st.spinner("해당 날짜의 본문을 찾는 중입니다..."):
        bible_data = get_bible_schedule(selected_date)
        results = bible_data.get("results", [])
        if not results: st.info(f"📅 {selected_date} : 아직 등록된 매일 성경 일정이 없습니다.")
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
    if st.button("🔄 최신 자료 불러오기", key="btn_admin"): st.rerun()
    st.divider()
    with st.spinner("자료를 불러오는 중입니다..."):
        pastor_data = get_pastor_data()
        results = pastor_data.get("results", [])
        if not results: st.info("아직 올라온 자료가 없습니다.")
        else:
            for page in results:
                try: title = page["properties"]["말씀과 기도"]["title"][0]["plain_text"]
                except: title = "제목 없음"
                try: content = page["properties"]["내용"]["rich_text"][0]["plain_text"]
                except: content = "내용이 없습니다."
                try: date_str = page["properties"]["날짜"]["date"]["start"]
                except: date_str = page["created_time"].split("T")[0]
                with st.expander(f"📅 {date_str} | {title}"): st.write(content)

# --- [탭 3] 나눔 작성하기 (성도용) ---
with tab3:
    st.write("공동체와 함께 감사와 기도제목을 나누는 공간입니다.")
    with st.form("share_form"):
        input_date = st.date_input("날짜", datetime.date.today())
        input_title = st.text_input("제목 (예: 오늘 하루도 지켜주심에 감사합니다)")
        input_category = st.selectbox("카테고리", ["묵상나눔", "감사나눔", "기도제목 나눔", "모두 나눔"])
        input_content = st.text_area("나눌 내용을 자유롭게 적어주세요", height=200)
        submitted = st.form_submit_button("나눔 등록하기")
    if submitted:
        if input_title == "" or input_content == "": st.warning("제목과 내용을 모두 입력해 주세요! 😅")
        else:
            status = send_to_notion(input_title, input_category, input_content, str(input_date))
            if status == 200:
                st.success(f"할렐루야! '{input_title}' 글이 등록되었습니다! 🎉")
                st.balloons()
            else: st.error(f"오류가 발생했어요. (에러 코드: {status})")

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
            except: cat = ""
            if cat in ["묵상나눔", "감사나눔", "기도제목 나눔", "모두 나눔"]: user_posts.append(p)
        if not user_posts: st.info("아직 등록된 나눔이 없습니다.")
        else:
            for page in user_posts:
                try: title = page["properties"]["이름"]["title"][0]["plain_text"]
                except: title = "제목 없음"
                try: category = page["properties"]["카테고리"]["select"]["name"]
                except: category = "분류 없음"
                try: content = page["properties"]["내용"]["rich_text"][0]["plain_text"]
                except: content = "내용이 없습니다."
                try: date_str = page["properties"]["날짜"]["date"]["start"]
                except: date_str = page["created_time"].split("T")[0]
                with st.expander(f"📅 {date_str} | [{category}] {title}"): st.write(content)