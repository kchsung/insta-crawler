import streamlit as st
import time
import re
import random
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd

# src 디렉토리의 InstagramCrawler 클래스 import
from src.instagram_crawler import InstagramCrawler

def single_crawl_tab():
    """단일 포스트 크롤링 탭"""
    st.subheader("📱 단일 포스트 크롤링")
    st.markdown("하나의 Instagram 포스트를 크롤링합니다.")
    
    # 디버그 모드 토글
    debug_mode = st.checkbox("🔍 디버그 모드", help="페이지의 HTML 요소들을 확인할 수 있습니다")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Instagram URL 입력")
        url = st.text_input(
            "Instagram 포스트 URL",
            placeholder="https://www.instagram.com/p/ABC123/",
            help="크롤링할 Instagram 포스트의 URL을 입력하세요"
        )
    
    with col2:
        st.subheader("크롤링 옵션")
        if st.button("🚀 크롤링 시작", type="primary"):
            if not url:
                st.error("URL을 입력해주세요!")
                return
            
            if 'instagram.com' not in url:
                st.error("올바른 Instagram URL을 입력해주세요!")
                return
            
            with st.spinner("크롤링 중..."):
                crawler = InstagramCrawler()
                result = crawler.crawl_instagram_post(url, debug_mode)
                crawler.close_driver()
            
            if result['status'] == 'success':
                st.success("크롤링이 완료되었습니다!")
                
                # 결과를 카드 형태로 표시
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="👍 좋아요",
                        value=f"{result['likes']:,}",
                        help="포스트의 좋아요 수"
                    )
                
                with col2:
                    st.metric(
                        label="💬 댓글",
                        value=f"{result['comments']:,}",
                        help="포스트의 댓글 수"
                    )
                
                with col3:
                    engagement = result['likes'] + result['comments']
                    st.metric(
                        label="📊 총 참여도",
                        value=f"{engagement:,}",
                        help="좋아요 + 댓글 수"
                    )
                
                # 상세 정보 표시
                with st.expander("📋 상세 정보"):
                    st.json(result)
                    
            elif result['status'] == 'timeout':
                st.error(f"⏰ 타임아웃: {result.get('error', '페이지 로딩 시간 초과')}")
            else:
                st.error(f"❌ 오류: {result.get('error', '알 수 없는 오류가 발생했습니다')}")

def batch_crawl_tab():
    """일괄 크롤링 탭"""
    st.subheader("📊 일괄 크롤링")
    st.markdown("엑셀 파일을 업로드하여 여러 Instagram 포스트를 한 번에 크롤링합니다.")
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "엑셀 파일 업로드",
        type=['xlsx', 'xls'],
        help="name과 instagram_link 컬럼이 포함된 엑셀 파일을 업로드하세요"
    )
    
    if uploaded_file is not None:
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(uploaded_file)
            
            # 필수 컬럼 확인
            required_columns = ['name', 'instagram_link']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"필수 컬럼이 없습니다: {', '.join(missing_columns)}")
                st.info("엑셀 파일에 다음 컬럼들이 포함되어야 합니다:")
                for col in required_columns:
                    st.write(f"- {col}")
                return
            
            # 유효한 데이터만 필터링
            valid_df = df.dropna(subset=['instagram_link'])
            valid_df = valid_df[valid_df['instagram_link'].str.contains('instagram.com', na=False)]
            
            st.success(f"✅ {len(valid_df)}개의 유효한 포스트를 찾았습니다!")
            
            # 미리보기
            st.subheader("📋 데이터 미리보기")
            st.dataframe(df.head(10), use_container_width=True)
            
            # 크롤링 시작 버튼
            if st.button("🚀 일괄 크롤링 시작", type="primary"):
                if len(valid_df) == 0:
                    st.error("크롤링할 유효한 데이터가 없습니다.")
                    return
                
                # 진행률 표시를 위한 컨테이너
                progress_container = st.container()
                status_container = st.container()
                results_container = st.container()
                
                with progress_container:
                    progress_bar = st.progress(0)
                    progress_text = st.empty()
                
                with status_container:
                    status_text = st.empty()
                
                # 크롤링 실행 (안전한 WebSocket 업데이트 사용)
                with results_container:
                    with st.spinner("일괄 크롤링을 시작합니다..."):
                        crawler = InstagramCrawler()
                        # 새로운 안전한 progress callback 사용
                        results = crawler.batch_crawl_instagram_posts(
                            valid_df, 
                            progress_callback=None,  # 기존 콜백 대신 안전한 방식 사용
                            progress_bar=progress_bar,
                            progress_text=progress_text,
                            status_text=status_text
                        )
                        crawler.close_driver()
                
                # 결과 표시
                st.success("일괄 크롤링이 완료되었습니다!")
                
                # 결과 데이터프레임 생성
                results_df = pd.DataFrame(results)
                
                # 통계 표시
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("총 포스트", len(results_df))
                with col2:
                    successful = len(results_df[results_df['status'] == 'success'])
                    st.metric("성공", successful)
                with col3:
                    failed = len(results_df[results_df['status'] != 'success'])
                    st.metric("실패", failed)
                with col4:
                    total_likes = results_df[results_df['status'] == 'success']['likes'].sum()
                    st.metric("총 좋아요", f"{total_likes:,}")
                
                # 결과 테이블
                st.subheader("📊 크롤링 결과")
                st.dataframe(results_df, use_container_width=True)
                
                # 결과 다운로드
                csv = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 결과 다운로드 (CSV)",
                    data=csv,
                    file_name=f"instagram_crawl_results_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

def main():
    """메인 함수"""
    st.set_page_config(
        page_title="Instagram 크롤러",
        page_icon="📱",
        layout="wide"
    )
    
    st.title("📱 Instagram 크롤러")
    st.markdown("Instagram 포스트의 좋아요와 댓글 수를 크롤링합니다.")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["🔍 단일 크롤링", "📊 일괄 크롤링"])
    
    with tab1:
        single_crawl_tab()
    
    with tab2:
        batch_crawl_tab()
    
    # 사이드바에 정보 표시
    with st.sidebar:
        st.header("ℹ️ 사용법")
        st.markdown("""
        ### 단일 크롤링
        1. Instagram 포스트 URL 입력
        2. 크롤링 시작 버튼 클릭
        3. 결과 확인
        
        ### 일괄 크롤링
        1. 엑셀 파일 업로드 (name, instagram_link 컬럼 필요)
        2. 데이터 미리보기 확인
        3. 일괄 크롤링 시작
        4. 결과 다운로드
        """)
        
        st.header("⚠️ 주의사항")
        st.markdown("""
        - Instagram의 정책을 준수하여 사용하세요
        - 과도한 요청은 차단될 수 있습니다
        - 개인정보 보호에 주의하세요
        """)

if __name__ == "__main__":
    main()