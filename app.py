import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import datetime
import time

# ==========================================
# 1. API 키 설정
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

def send_to_notion(title, category, content, date_str, author):
    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "이름": { "title": [{"text": {"content": title}}] },
            "카테고리": { "select": {"name": category} },
            "날짜": { "date": {"start": date_str} },
            "작성자": { "rich_text": [{"text": {"content": author}}] },
            "내용": { "rich_text": [{"text": {"content": content}}] }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code

def update_notion_page(page_id, properties):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    data = {"properties": properties}
    requests.patch(url, headers=headers, data=json.dumps(data))

def get_from_notion():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"sorts": [{"timestamp": "created_time", "direction": "descending"}]}
    return requests.post(url, headers=headers, json=payload).json()

def get_bible_schedule(target_date):
    url = f"https://api.notion.com/v1/databases/{BIBLE_DB_ID}/query"
    payload = {"filter": {"property": "날짜", "date": {"equals": str(target_date)}}}
    return requests.post(url, headers=headers, json=payload).json()

def get_pastor_data():
    url = f"https://api.notion.com/v1/databases/{PASTOR_DB_ID}/query"
    payload = {"sorts": [{"timestamp": "created_time", "direction": "descending"}]}
    return requests.post(url, headers=headers, json=payload).json()

def get_smart_scroll_html(box_id, height, content):
    # 💡 글이 끝났을 때 바로 훅! 올라가지 않고 살짝 여유(padding-bottom 80px)를 주었습니다.
    return f"""
    <div id="{box_id}" class="smart-scroll-box" style="height: {height}px; overflow-y: auto;">
        <div style="display: flex; flex-direction: column; gap: 15px; padding-bottom: 80px;">
            {content}
        </div>
    </div>
    """

# ==========================================
# 2. 어플 화면 그리기 및 UI
# ==========================================
st.set_page_config(page_title="토다 나눔방", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    .smart-scroll-box { padding: 15px; background: white; border: 1px solid #eee; border-radius: 0 0 10px 10px; }
    .smart-scroll-box::-webkit-scrollbar { width: 6px; }
    .smart-scroll-box::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px;}
    .smart-scroll-box::-webkit-scrollbar-thumb { background: #ccc; border-radius: 10px; }
    .board-title { font-weight: bold; text-align: center; padding: 12px; border-radius: 10px 10px 0 0; color: #333; margin-bottom: 0; }
    .post-item { border-bottom: 1px dashed #ddd; padding-bottom: 10px; margin-bottom: 10px; font-size: 0.95em; line-height: 1.5; }

    /* ==========================================================
       💻📱 반응형(화면 크기 자동 감지) 설정
       - 접속한 기기의 화면 너비를 브라우저가 스스로 보고
         웹(넓게) / 핸드폰(좁게) 레이아웃을 자동으로 선택합니다.
       ========================================================== */

    /* [기본/데스크탑] 웹에서는 화면을 시원하게 꽉 채워서 보여줍니다. */
    .block-container {
        max-width: 1400px !important;
        padding-top: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }

    /* [태블릿] 너비 1024px 이하 */
    @media (max-width: 1024px) {
        .block-container {
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
    }

    /* [핸드폰] 너비 768px 이하 - 여백을 줄이고 글상자 높이를
       화면 높이에 맞게 자동으로 조절합니다. */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
        /* 고정 픽셀 높이 대신 화면 높이 기준(vh)으로 자동 조절 */
        .smart-scroll-box {
            height: auto !important;
            max-height: 45vh !important;
            padding: 12px !important;
        }
        h1 { font-size: 1.6rem !important; }
        .board-title { padding: 8px !important; font-size: 0.95em !important; }
        .post-item { font-size: 0.9em !important; }
    }
</style>
""", unsafe_allow_html=True)

now = int(time.time())
st.markdown(f'<a href="/?v={now}" target="_self" style="text-decoration: none; color: inherit;"><h1 style="margin-bottom: 0px; cursor: pointer;">🌿 토다 공동체 나눔방</h1></a>', unsafe_allow_html=True)
st.subheader("예수님을 닮아가는 우리의 매일의 기록")

tab0, tab1, tab2, tab3, tab4 = st.tabs(["🏠 토다 광장", "📖 매일 성경", "🙏 말씀과 기도", "📝 나눔 작성", "💬 나눔 모아보기"])

# --- [탭 0] 🏠 토다 광장 ---
with tab0:
    st.write("오늘의 말씀과 공동체의 나눔을 한눈에 확인하세요!")
    today = datetime.date.today()
    three_days_ago = today - datetime.timedelta(days=3)
    
    with st.spinner("광장 전광판을 불러오는 중입니다... 🎨"):
        bible_res = get_bible_schedule(today).get("results", [])
        pastor_res = get_pastor_data().get("results", [])
        user_res = get_from_notion().get("results", [])
        
        bible_title, bible_verses = "오늘의 말씀이 없습니다.", "등록된 성경 본문이 없습니다."
        if bible_res:
            try: bible_title = bible_res[0]["properties"]["이름"]["title"][0]["plain_text"]
            except: pass
            try: bible_verses = bible_res[0]["properties"]["본문"]["rich_text"][0]["plain_text"]
            except: pass
            
        pastor_title, pastor_content = "묵상 자료가 없습니다.", ""
        if pastor_res:
            try: pastor_title = pastor_res[0]["properties"]["말씀과 기도"]["title"][0]["plain_text"]
            except: pass
            try: pastor_content = pastor_res[0]["properties"]["내용"]["rich_text"][0]["plain_text"]
            except: pass

        muksang_list, gamsa_list, gido_list = "", "", ""
        for p in user_res:
            try: cat = p["properties"]["카테고리"]["select"]["name"]
            except: cat = ""
            try: date_str = p["properties"]["날짜"]["date"]["start"]
            except: date_str = p["created_time"].split("T")[0]
            
            try:
                if datetime.datetime.strptime(date_str, "%Y-%m-%d").date() < three_days_ago: continue
            except: pass
            
            try: title = p["properties"]["이름"]["title"][0]["plain_text"]
            except: title = "제목 없음"
            try: content = p["properties"]["내용"]["rich_text"][0]["plain_text"]
            except: content = ""
            try: author = p["properties"]["작성자"]["rich_text"][0]["plain_text"]
            except: author = "익명"
            
            html_item = f'<div class="post-item"><b style="color:#0056b3;">[{title} | {author}]</b><br>{content.replace(chr(10), "<br>")}</div>'
            
            if cat == "묵상나눔": muksang_list += html_item
            elif cat == "감사나눔": gamsa_list += html_item
            elif cat == "기도제목 나눔": gido_list += html_item

        if not muksang_list: muksang_list = "<div class='post-item'>최근 3일간 올라온 묵상 나눔이 없습니다.</div>"
        if not gamsa_list: gamsa_list = "<div class='post-item'>최근 3일간 올라온 감사 나눔이 없습니다.</div>"
        if not gido_list: gido_list = "<div class='post-item'>최근 3일간 올라온 기도제목이 없습니다.</div>"

        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col1:
            st.markdown(f'<div class="board-title" style="background-color: #ffd54f;">📖 [ 오늘의 성경 본문 ]<br>{bible_title}</div>', unsafe_allow_html=True)
            st.markdown(get_smart_scroll_html("scroll_bible", 550, bible_verses.replace(chr(10), "<br>")), unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="board-title" style="background-color: #a5d6a7;">🌿 [ 오늘의 성경 본문 묵상 자료 ]</div>', unsafe_allow_html=True)
            # 수동 스크롤 박스 (크기 380px)
            st.markdown(f'<div class="smart-scroll-box" style="height: 380px; overflow-y: auto;"><b>[{pastor_title}]</b><br><br>{pastor_content.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            
            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
            
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.markdown('<div class="board-title" style="background-color: #e1bee7;">🙏 감사나눔</div>', unsafe_allow_html=True)
                st.markdown(get_smart_scroll_html("scroll_gamsa", 130, gamsa_list), unsafe_allow_html=True)
            with col2_2:
                st.markdown('<div class="board-title" style="background-color: #bbdefb;">💌 기도제목 나눔</div>', unsafe_allow_html=True)
                st.markdown(get_smart_scroll_html("scroll_gido", 130, gido_list), unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="board-title" style="background-color: #ffcc80;">💬 [ 말씀 묵상 나눔 ]</div>', unsafe_allow_html=True)
            st.markdown(get_smart_scroll_html("scroll_muksang", 550, muksang_list), unsafe_allow_html=True)

    # 💡 모터 스크립트: 4개의 구역이 멈추지 않고 부드럽게 돌아갑니다!
    components.html(
        """
        <script>
        function startAutoScroll() {
            const parentDoc = window.parent.document;
            const boxes = [
                {id: 'scroll_bible', speed: 40},
                {id: 'scroll_gamsa', speed: 40},
                {id: 'scroll_gido', speed: 40},
                {id: 'scroll_muksang', speed: 40} // 말씀 묵상 나눔도 완벽 등록!
            ];
            
            boxes.forEach(item => {
                const box = parentDoc.getElementById(item.id);
                if (box && box.dataset.init !== '1') {
                    box.dataset.init = '1';
                    let isHovered = false;
                    
                    box.addEventListener('mouseenter', () => isHovered = true);
                    box.addEventListener('mouseleave', () => isHovered = false);
                    box.addEventListener('touchstart', () => isHovered = true);
                    box.addEventListener('touchend', () => setTimeout(() => isHovered=false, 1500));
                    
                    setInterval(() => {
                        // 💡 글이 길어서 '진짜 스크롤'이 생겼을 때만 모터가 작동합니다!
                        if (!isHovered && box.scrollHeight > box.clientHeight) {
                            box.scrollTop += 1;
                            if (Math.ceil(box.scrollTop) + box.clientHeight >= box.scrollHeight) {
                                box.scrollTop = 0;
                            }
                        }
                    }, item.speed);
                }
            });
        }
        setTimeout(startAutoScroll, 1000);
        </script>
        """,
        height=0, width=0
    )

# --- [탭 1] 매일 성경 ---
with tab1:
    st.subheader("📖 달력을 눌러 매일 성경을 확인하세요")
    selected_date = st.date_input("날짜 선택", datetime.date.today())
    st.divider()
    with st.spinner("해당 날짜의 본문을 찾는 중입니다..."):
        bible_data = get_bible_schedule(selected_date).get("results", [])
        if not bible_data: st.info(f"📅 {selected_date} : 등록된 일정이 없습니다.")
        else:
            for page in bible_data:
                try: title = page["properties"]["이름"]["title"][0]["plain_text"]
                except: title = "제목 없음"
                try: verses = page["properties"]["본문"]["rich_text"][0]["plain_text"]
                except: verses = "본문 없음"
                st.success(f"**오늘의 주제:** {title}")
                st.write(f"📖 **읽을 본문:** {verses}")

def render_post_with_reactions(page, title_key, category_key=None):
    page_id = page["id"]
    try: title = page["properties"][title_key]["title"][0]["plain_text"]
    except: title = "제목 없음"
    category_str = ""
    if category_key:
        try: category_str = f"[{page['properties'][category_key]['select']['name']}] "
        except: pass
    try: content = page["properties"]["내용"]["rich_text"][0]["plain_text"]
    except: content = "내용이 없습니다."
    try: date_str = page["properties"]["날짜"]["date"]["start"]
    except: date_str = page["created_time"].split("T")[0]
    try: author = page["properties"]["작성자"]["rich_text"][0]["plain_text"]
    except: author = "익명"

    try: reactions = json.loads(page["properties"]["공감"]["rich_text"][0]["plain_text"])
    except: reactions = {"👍":0, "🙏":0, "❤️":0, "✨":0, "😊":0, "💡":0, "🙌":0}
    
    try: comments = json.loads(page["properties"]["댓글"]["rich_text"][0]["plain_text"])
    except: comments = []

    with st.expander(f"📅 {date_str} | {category_str}{title} (✍️ {author})"):
        st.write(content)
        st.divider()
        
        emojis = ["👍", "🙏", "❤️", "✨", "😊", "💡", "🙌"]
        cols = st.columns(7)
        for i, em in enumerate(emojis):
            count = reactions.get(em, 0)
            if cols[i].button(f"{em} {count}", key=f"emo_{page_id}_{em}"):
                reactions[em] = count + 1
                update_data = { "공감": { "rich_text": [{"text": {"content": json.dumps(reactions, ensure_ascii=False)}}] } }
                update_notion_page(page_id, update_data)
                st.rerun()
                
        if comments:
            st.markdown("---")
            for c in comments:
                st.markdown(f"💬 **{c['name']}**: {c['msg']}")
                
        with st.form(f"comment_form_{page_id}"):
            c1, c2 = st.columns([1, 4])
            with c1: c_name = st.text_input("이름", key=f"cname_{page_id}")
            with c2: c_msg = st.text_input("댓글 남기기", key=f"cmsg_{page_id}")
            c_submit = st.form_submit_button("댓글 등록")
            if c_submit and c_name and c_msg:
                comments.append({"name": c_name, "msg": c_msg})
                update_data = { "댓글": { "rich_text": [{"text": {"content": json.dumps(comments, ensure_ascii=False)}}] } }
                update_notion_page(page_id, update_data)
                st.rerun()

# --- [탭 2] 말씀과 기도 (관리자 전용 읽기) ---
with tab2:
    st.subheader("🙏 목회자 나눔 (말씀과 기도)")
    if st.button("🔄 최신 자료 불러오기", key="btn_admin"): st.rerun()
    st.divider()
    with st.spinner("자료를 불러오는 중입니다..."):
        pastor_res = get_pastor_data().get("results", [])
        if not pastor_res: st.info("아직 올라온 자료가 없습니다.")
        else:
            for page in pastor_res:
                render_post_with_reactions(page, title_key="말씀과 기도")

# --- [탭 3] 나눔 작성하기 (성도용) ---
with tab3:
    st.write("공동체와 함께 감사와 기도제목을 나누는 공간입니다.")
    with st.form("share_form"):
        col1, col2 = st.columns(2)
        with col1: input_date = st.date_input("날짜", datetime.date.today())
        with col2: input_author = st.text_input("✍️ 작성자 이름 (필수)", placeholder="예: 홍길동 청년")
        
        input_title = st.text_input("제목 (예: 오늘 하루도 지켜주심에 감사합니다)")
        input_category = st.selectbox("카테고리", ["묵상나눔", "감사나눔", "기도제목 나눔", "모두 나눔"])
        input_content = st.text_area("나눌 내용을 자유롭게 적어주세요", height=200)
        submitted = st.form_submit_button("나눔 등록하기")
        
    if submitted:
        if input_title == "" or input_content == "" or input_author == "":
            st.warning("작성자, 제목, 내용을 모두 입력해 주세요! 😅")
        else:
            status = send_to_notion(input_title, input_category, input_content, str(input_date), input_author)
            if status == 200:
                st.success(f"할렐루야! '{input_author}'님의 글이 등록되었습니다! 🎉")
                st.balloons()
            else: st.error(f"오류가 발생했어요. (에러 코드: {status})")

# --- [탭 4] 나눔 모아보기 (성도용) ---
with tab4:
    st.write("지체들이 남긴 은혜로운 나눔을 확인해 보세요!")
    if st.button("🔄 최신 나눔 불러오기", key="btn_user"): st.rerun()
    st.divider()
    with st.spinner("나눔을 불러오는 중입니다..."):
        user_res = get_from_notion().get("results", [])
        filtered_posts = []
        for p in user_res:
            try: cat = p["properties"]["카테고리"]["select"]["name"]
            except Exception: cat = ""
            if cat in ["묵상나눔", "감사나눔", "기도제목 나눔", "모두 나눔"]:
                filtered_posts.append(p)
        
        if not filtered_posts: st.info("아직 등록된 나눔이 없습니다.")
        else:
            for page in filtered_posts:
                render_post_with_reactions(page, title_key="이름", category_key="카테고리")