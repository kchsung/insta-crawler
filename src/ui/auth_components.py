import streamlit as st
from typing import Dict, Any
from ..supabase.auth import supabase_auth

def render_login_form() -> Dict[str, Any]:
    """로그인 폼 렌더링"""
    st.subheader("🔐 로그인")
    
    with st.form("login_form"):
        email = st.text_input("이메일", placeholder="your@email.com")
        password = st.text_input("비밀번호", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_submitted = st.form_submit_button("로그인", type="primary")
        with col2:
            forgot_password = st.form_submit_button("비밀번호 찾기")
        
        if login_submitted:
            if not email or not password:
                st.error("이메일과 비밀번호를 입력해주세요.")
                return {"action": "none"}
            
            with st.spinner("로그인 중..."):
                result = supabase_auth.sign_in(email, password)
                
            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])
            
            return {"action": "login", "result": result}
        
        if forgot_password:
            if not email:
                st.error("이메일을 입력해주세요.")
                return {"action": "none"}
            
            with st.spinner("비밀번호 재설정 이메일 발송 중..."):
                result = supabase_auth.reset_password(email)
                
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result["message"])
            
            return {"action": "reset_password", "result": result}
    
    return {"action": "none"}

def render_signup_form() -> Dict[str, Any]:
    """회원가입 폼 렌더링"""
    st.subheader("📝 회원가입")
    
    with st.form("signup_form"):
        email = st.text_input("이메일", placeholder="your@email.com")
        password = st.text_input("비밀번호", type="password")
        confirm_password = st.text_input("비밀번호 확인", type="password")
        
        signup_submitted = st.form_submit_button("회원가입", type="primary")
        
        if signup_submitted:
            if not email or not password or not confirm_password:
                st.error("모든 필드를 입력해주세요.")
                return {"action": "none"}
            
            if password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
                return {"action": "none"}
            
            if len(password) < 6:
                st.error("비밀번호는 최소 6자 이상이어야 합니다.")
                return {"action": "none"}
            
            with st.spinner("회원가입 중..."):
                result = supabase_auth.sign_up(email, password)
                
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result["message"])
            
            return {"action": "signup", "result": result}
    
    return {"action": "none"}

def render_auth_sidebar():
    """인증 관련 사이드바 렌더링"""
    with st.sidebar:
        st.header("🔐 인증")
        
        if supabase_auth.is_authenticated():
            user = supabase_auth.get_current_user()
            st.success(f"로그인됨: {user.email}")
            
            if st.button("로그아웃", type="secondary"):
                result = supabase_auth.sign_out()
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])
        else:
            st.info("로그인이 필요합니다.")
            
            # 탭으로 로그인/회원가입 구분
            tab1, tab2 = st.tabs(["로그인", "회원가입"])
            
            with tab1:
                render_login_form()
            
            with tab2:
                render_signup_form()

def render_user_profile():
    """사용자 프로필 표시"""
    if supabase_auth.is_authenticated():
        user = supabase_auth.get_current_user()
        
        st.subheader("👤 사용자 정보")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("이메일", user.email)
            st.metric("가입일", user.created_at[:10] if user.created_at else "N/A")
        
        with col2:
            st.metric("마지막 로그인", user.last_sign_in_at[:10] if user.last_sign_in_at else "N/A")
            st.metric("이메일 확인", "✅" if user.email_confirmed_at else "❌")
        
        # 사용자 통계 표시
        from ..db.database import db_manager
        user_stats = db_manager.get_user_stats()
        
        if user_stats:
            st.subheader("📊 크롤링 통계")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 세션", user_stats.get('total_sessions', 0))
            with col2:
                st.metric("총 포스트", user_stats.get('total_posts', 0))
            with col3:
                st.metric("성공한 포스트", user_stats.get('successful_posts', 0))
            with col4:
                st.metric("총 좋아요", f"{user_stats.get('total_likes', 0):,}")
            
            if user_stats.get('last_crawl_date'):
                st.info(f"마지막 크롤링: {user_stats['last_crawl_date'][:10]}")
        else:
            st.info("아직 크롤링 통계가 없습니다.")
    else:
        st.warning("로그인이 필요합니다.")
