import streamlit as st
import sys
import os

# ── Page config: 모든 st.* 호출보다 우선 ─────────────────────────
st.set_page_config(
    page_title="Instagram Crawler",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Path ─────────────────────────────────────────────────────
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.auth_components import render_auth_sidebar, render_user_profile  # (미사용 시 삭제해도 됨)
from src.ui.crawler_components import render_single_crawl_form, render_batch_crawl_form, render_crawl_history  # (미사용 시 삭제해도 됨)
from src.ui.project_components import (
    render_single_url_crawl, render_batch_url_crawl,
    render_project_management, render_performance_management
)
from src.supabase.auth import supabase_auth


# ── CSS ──────────────────────────────────────────────────────
def load_css_file():
    css_file = os.path.join(os.path.dirname(__file__), 'css', 'main.css')
    if os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def inject_layout_css():
    st.markdown("""
    <style>
    /* ===== 레이아웃 & 여백 조정 ===== */

    /* 본문 컨테이너: 상단여백 완전 제거 + 좌우 패딩 컴팩트 + 전체폭 */
    section.main > div.block-container {
        max-width: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding-top: 0 !important;           /* ⬅ 상단 여백 0 */
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    /* 첫 요소(타이틀/탭 등) 위 여백까지 0 */
    section.main > div.block-container > :first-child { margin-top: 0 !important; }

    /* 제목 기본 마진 완전 제거 */
    h1, h2, h3 { margin-top: 0 !important; margin-bottom: 0.5rem !important; }

    /* 탭 상단 여백 제거 */
    div[data-baseweb="tab-list"] { margin-top: 0 !important; }

    /* 가로 블록이 중앙 정렬되는 문제 방지 */
    div[data-testid="stHorizontalBlock"] { justify-content: flex-start !important; }

    /* ===== 사이드바 토글 정상작동 보장 =====
       - transform 강제 해제(기존 토글과 충돌 X)
       - 펼침(true)일 때만 폭 지정, 접힘(false)일 때는 프레임워크 기본 동작 유지
    */
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 260px !important;
        max-width: 280px !important;
        width: 280px !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        width: 0 !important;
        min-width: 0 !important;
        /* transform/translate는 프레임워크에 맡김 */
    }

    /* ===== 버튼/텍스트 미관 보정 ===== */

     /* 모든 버튼 한 줄 유지 (비밀번호 찾기 등) */
     div.stButton > button { white-space: nowrap !important; }
     
     /* 폼 버튼 크기 통일 */
     .stForm .stButton > button {
         min-height: 2.5rem !important;
         font-size: 0.95rem !important;
         font-weight: 600 !important;
     }

    /* 로그인 성공 배지: 한 줄, 넘치면 말줄임 */
    .login-ok {
        background: #e9f7ef;
        border: 1px solid #d4edda;
        color: #155724;
        padding: .6rem .75rem;
        border-radius: .5rem;
        font-size: .95rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .login-ok .email { font-weight: 600; }

    /* 사이드바 헤드라인(로고 영역) 줄바꿈 방지 */
    .sidebar-title { white-space: nowrap; }

    /* 필요 시 상단 헤더를 숨기지 않음(접힘 버튼 살리기) */
    /* #MainMenu만 숨기고, header/footer는 유지 */
    #MainMenu { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

def load_css():
    load_css_file()     # 프로젝트 CSS
    inject_layout_css() # 레이아웃/사이드바/버튼/배지 CSS


# ── Sidebar ──────────────────────────────────────────────────
def render_login_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; margin-bottom: 1rem;" class="sidebar-title">
            <div style="margin-bottom: .5rem;">
                <img src="https://zttosbzbwkgqkpsdgpcx.supabase.co/storage/v1/object/public/connecta/connecta_logo.svg"
                     alt="Connecta Logo"
                     style="height: 40px; width: auto; max-width: 120px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">
            </div>
            <h3 style="margin: 0; color: #667eea; font-size: 1.3rem; font-weight: 600;">관리도구</h3>
        </div>
        """, unsafe_allow_html=True)

        # 임시로 로그인 기능 비활성화 (개발 편의성)
        st.markdown(
            """<div class="login-ok">🔧 개발 모드: 로그인 비활성화</div>""",
            unsafe_allow_html=True
        )
        
        # 로그인 관련 코드 주석 처리
        # if supabase_auth.is_authenticated():
        #     user = supabase_auth.get_current_user()
        #     # ✅ 커스텀 배지 (한 줄/말줄임)
        #     st.markdown(
        #         f"""<div class="login-ok">✅ 로그인됨: <span class="email">{user.email}</span></div>""",
        #         unsafe_allow_html=True
        #     )
        #     st.button("🚪 로그아웃", type="secondary", use_container_width=True, key="logout_btn")
        #     if st.session_state.get("logout_btn"):
        #         result = supabase_auth.sign_out()
        #         if result["success"]:
        #             st.success(result["message"])
        #             st.rerun()
        #         else:
        #             st.error(result["message"])
        # else:
        #     st.info("로그인이 필요합니다")
        #     tab1, tab2 = st.tabs(["로그인", "회원가입"])

        #     with tab1:
        #         with st.form("login_form"):
        #             email = st.text_input("이메일", placeholder="your@email.com")
        #             password = st.text_input("비밀번호", type="password")
                    
        #             # 버튼들을 상하로 배치하고 입력 필드와 같은 가로 길이로 설정
        #             do_login = st.form_submit_button("로그인", type="primary", use_container_width=True)
        #             do_reset = st.form_submit_button("비밀번호 찾기", use_container_width=True)

        #             if do_login:
        #                 if not email or not password:
        #                     st.error("이메일과 비밀번호를 입력해주세요.")
        #                 else:
        #                     with st.spinner("로그인 중..."):
        #                         result = supabase_auth.sign_in(email, password)
        #                     if result["success"]:
        #                         st.success(result["message"])
        #                         st.rerun()
        #                     else:
        #                         st.error(result["message"])

        #             if do_reset:
        #                 if not email:
        #                     st.error("이메일을 입력해주세요.")
        #                 else:
        #                     with st.spinner("비밀번호 재설정 이메일 발송 중..."):
        #                         result = supabase_auth.reset_password(email)
        #                     if result["success"]:
        #                         st.success(result["message"])
        #                     else:
        #                         st.error(result["message"])

        #     with tab2:
        #         with st.form("signup_form"):
        #             email = st.text_input("이메일", placeholder="your@email.com", key="signup_email")
        #             password = st.text_input("비밀번호", type="password", key="signup_password")
        #             confirm = st.text_input("비밀번호 확인", type="password", key="signup_confirm")
                    
        #             # 회원가입 버튼도 입력 필드와 같은 가로 길이로 설정
        #             do_signup = st.form_submit_button("회원가입", type="primary", use_container_width=True)

        #             if do_signup:
        #                 if not email or not password or not confirm:
        #                     st.error("모든 필드를 입력해주세요.")
        #                 elif password != confirm:
        #                     st.error("비밀번호가 일치하지 않습니다.")
        #                 elif len(password) < 6:
        #                     st.error("비밀번호는 최소 6자 이상이어야 합니다.")
        #                 else:
        #                     with st.spinner("회원가입 중..."):
        #                         result = supabase_auth.sign_up(email, password)
        #                     if result["success"]:
        #                         st.success(result["message"])
        #                         st.rerun()
        #                     else:
        #                         st.error(result["message"])


# ── Main content ─────────────────────────────────────────────
def render_main_content():
    # 임시로 로그인 체크 비활성화 (개발 편의성)
    # if not supabase_auth.is_authenticated():
    #     st.markdown("""
    #     <div style="text-align:left; margin:0; padding:0;">
    #         <p style="font-size:1.05rem; color:#6c757d; margin:.5rem 0 0;">
    #             Instagram 크롤링 기능을 사용하려면 먼저 로그인해주세요.
    #         </p>
    #     </div>
    #     """, unsafe_allow_html=True)
    #     return

    tab1, tab2, tab3, tab4 = st.tabs(["🔍 단일 URL 크롤링", "📊 복수 URL 크롤링", "📋 프로젝트 관리", "📈 성과 관리"])
    with tab1:
        render_single_url_crawl()
    with tab2:
        render_batch_url_crawl()
    with tab3:
        render_project_management()
    with tab4:
        render_performance_management()


# ── App ──────────────────────────────────────────────────────
def main():
    load_css()                # 프로젝트 CSS + 위 레이아웃 CSS

    # 임시로 인증 상태 초기화 비활성화 (개발 편의성)
    # if 'authenticated' not in st.session_state:
    #     st.session_state.authenticated = False

    render_login_sidebar()    # 실제 st.sidebar 렌더
    render_main_content()     # 본문

    st.markdown("""
    <div style="text-align:center; margin-top: 2rem; padding: 1.25rem; color:#6c757d; border-top:1px solid #e9ecef;">
        <p style="margin:0;">⚠️ 이 도구는 교육 및 연구 목적으로만 사용하세요. Instagram의 이용약관을 준수해야 합니다.</p>
        <p style="font-size:.9rem; margin:.35rem 0 0;">Made with ❤️ using Streamlit & Supabase</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
