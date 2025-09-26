import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from ..instagram_crawler import InstagramCrawler
from ..db.database import db_manager
from ..db.models import InstagramCrawlResult

def render_single_crawl_form() -> Dict[str, Any]:
    """단일 포스트 크롤링 폼 렌더링"""
    st.subheader("📱 단일 포스트 크롤링")
    st.markdown("하나의 Instagram 포스트를 크롤링합니다.")
    
    # 디버그 모드 토글
    debug_mode = st.checkbox("🔍 디버그 모드", help="페이지의 HTML 요소들을 확인할 수 있습니다", key="single_post_debug_mode")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Instagram URL 입력")
        url = st.text_input(
            "Instagram 포스트 URL을 입력하세요:",
            placeholder="https://www.instagram.com/p/...",
            help="Instagram 포스트의 전체 URL을 입력해주세요"
        )
        
        if st.button("🔍 크롤링 시작", type="primary", key="single_post_crawl_start"):
            if not url:
                st.error("URL을 입력해주세요!")
                return {"action": "error", "message": "URL을 입력해주세요!"}
            elif "instagram.com" not in url:
                st.error("올바른 Instagram URL을 입력해주세요!")
                return {"action": "error", "message": "올바른 Instagram URL을 입력해주세요!"}
            else:
                with st.spinner(""):
                    crawler = InstagramCrawler()
                    result = crawler.crawl_instagram_post(url, debug_mode)
                    crawler.close_driver()
                
                # 결과 표시
                if result['status'] == 'success':
                    st.success("크롤링이 완료되었습니다!")
                    
                    # 결과를 카드 형태로 표시
                    col_likes, col_comments = st.columns(2)
                    
                    with col_likes:
                        st.metric(
                            label="❤️ 좋아요 수",
                            value=f"{result['likes']:,}",
                            help="이 포스트의 좋아요 수입니다"
                        )
                    
                    with col_comments:
                        st.metric(
                            label="💬 댓글 수",
                            value=f"{result['comments']:,}",
                            help="이 포스트의 댓글 수입니다"
                        )
                    
                    # 데이터베이스에 저장
                    crawl_result = InstagramCrawlResult(
                        post_name=f"Single Crawl - {url.split('/')[-2]}",
                        post_url=url,
                        likes=result['likes'],
                        comments=result['comments'],
                        status=result['status']
                    )
                    
                    save_result = db_manager.save_instagram_crawl_result(crawl_result)
                    if save_result["success"]:
                        st.info("결과가 데이터베이스에 저장되었습니다.")
                    
                    # 데이터프레임으로 표시
                    df = pd.DataFrame([{
                        'URL': result['url'],
                        '좋아요 수': result['likes'],
                        '댓글 수': result['comments']
                    }])
                    
                    st.subheader("📊 결과 요약")
                    st.dataframe(df, use_container_width=True)
                    
                    # CSV 다운로드 버튼
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 CSV 다운로드",
                        data=csv,
                        file_name="instagram_crawl_result.csv",
                        mime="text/csv"
                    )
                    
                    return {"action": "success", "data": result}
                    
                else:
                    st.error(f"크롤링 실패: {result.get('error', '알 수 없는 오류')}")
                    return {"action": "error", "data": result}
    
    with col2:
        st.subheader("📈 통계")
        st.info("""
        **추출 가능한 정보:**
        - ❤️ 좋아요 수 (예: "84 likes")
        - 💬 댓글 수 (예: "View all 30 comments")
        
        **지원 형식:**
        - 숫자 (예: 1,234)
        - K 단위 (예: 1.2K)
        - M 단위 (예: 1.5M)
        """)
        
        st.subheader("⚠️ 주의사항")
        st.warning("""
        - Instagram의 이용약관을 준수하세요
        - 과도한 요청은 계정 제재를 받을 수 있습니다
        - 비공개 계정의 포스트는 접근할 수 없습니다
        """)
    
    return {"action": "none"}

def render_batch_crawl_form() -> Dict[str, Any]:
    """일괄 크롤링 폼 렌더링"""
    st.subheader("📊 일괄 크롤링")
    st.markdown("엑셀 파일을 업로드하여 여러 Instagram 포스트를 일괄 크롤링합니다.")
    
    # 엑셀 파일 업로드
    uploaded_file = st.file_uploader(
        "엑셀 파일을 업로드하세요",
        type=['xlsx', 'xls'],
        help="A열: name, B열: instagram_link 형식의 엑셀 파일"
    )
    
    if uploaded_file is not None:
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(uploaded_file)
            
            # 빈 행 제거
            df = df.dropna(how='all')
            
            # 컬럼명 확인 및 수정
            if len(df.columns) >= 2:
                df.columns = ['name', 'instagram_link'] + list(df.columns[2:])
            else:
                st.error("엑셀 파일에 최소 2개의 컬럼(name, instagram_link)이 필요합니다.")
                return {"action": "error", "message": "엑셀 파일 형식이 올바르지 않습니다."}
            
            # 유효한 데이터만 필터링 (instagram_link가 있는 행만)
            valid_df = df.dropna(subset=['instagram_link'])
            valid_df = valid_df[valid_df['instagram_link'].astype(str).str.contains('instagram.com', na=False)]
            
            st.success(f"엑셀 파일이 성공적으로 로드되었습니다. 총 {len(df)}개 행 중 {len(valid_df)}개의 유효한 포스트가 있습니다.")
            
            if len(valid_df) == 0:
                st.warning("유효한 Instagram URL이 없습니다. URL이 올바른지 확인해주세요.")
                return {"action": "error", "message": "유효한 Instagram URL이 없습니다."}
            
            # 데이터 미리보기
            st.subheader("📋 데이터 미리보기")
            st.dataframe(df.head(10), use_container_width=True)
            
            # 크롤링 세션 생성
            session_name = st.text_input("세션 이름", value=f"Batch Crawl - {len(valid_df)} posts", key="excel_batch_session_name")
            
            # 크롤링 시작 버튼
            if st.button("🚀 일괄 크롤링 시작", type="primary", key="batch_crawl_start_excel"):
                if len(valid_df) == 0:
                    st.error("크롤링할 유효한 데이터가 없습니다.")
                    return {"action": "error", "message": "크롤링할 유효한 데이터가 없습니다."}
                
                # 크롤링 세션 생성
                session_result = db_manager.create_instagram_crawl_session(session_name, len(valid_df))
                session_id = None
                if session_result["success"]:
                    session_id = session_result["data"][0]["id"]
                    st.info(f"Instagram 크롤링 세션이 생성되었습니다. (ID: {session_id})")
                
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
                    with st.spinner(""):
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
                
                # 결과를 데이터베이스에 저장
                successful_posts = 0
                failed_posts = 0
                
                for result in results:
                    crawl_result = InstagramCrawlResult(
                        session_id=session_id,
                        post_name=result['name'],
                        post_url=result['url'],
                        likes=result['likes'],
                        comments=result['comments'],
                        status=result['status'],
                        error_message=result.get('error', '')
                    )
                    
                    save_result = db_manager.save_instagram_crawl_result(crawl_result)
                    if save_result["success"]:
                        if result['status'] == 'success':
                            successful_posts += 1
                        else:
                            failed_posts += 1
                
                # 세션 업데이트
                if session_id:
                    db_manager.update_instagram_crawl_session(session_id, successful_posts, failed_posts, "completed")
                
                # 결과 표시
                st.success("일괄 크롤링이 완료되었습니다!")
                
                # 결과 데이터프레임 생성
                results_df = pd.DataFrame(results)
                
                # 통계 표시
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("총 포스트", len(results_df))
                with col2:
                    success_count = len(results_df[results_df['status'] == 'success'])
                    st.metric("성공", success_count)
                with col3:
                    error_count = len(results_df[results_df['status'] == 'error'])
                    st.metric("실패", error_count)
                with col4:
                    total_likes = results_df[results_df['status'] == 'success']['likes'].sum()
                    st.metric("총 좋아요", f"{total_likes:,}")
                
                # 결과 테이블 표시
                st.subheader("📊 크롤링 결과")
                st.dataframe(results_df, use_container_width=True)
                
                # CSV 다운로드
                csv = results_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 결과 CSV 다운로드",
                    data=csv,
                    file_name="instagram_batch_crawl_results.csv",
                    mime="text/csv"
                )
                
                # 에러가 있는 경우 상세 표시
                error_results = results_df[results_df['status'] == 'error']
                if len(error_results) > 0:
                    st.subheader("⚠️ 에러 상세 정보")
                    st.dataframe(error_results[['name', 'url', 'error']], use_container_width=True)
                
                return {"action": "success", "data": results}
        
        except Exception as e:
            st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {str(e)}")
            return {"action": "error", "message": str(e)}
    
    # 사용법 안내
    st.subheader("📝 사용법")
    st.markdown("""
    ### 엑셀 파일 형식
    - **A열**: name (포스트 이름 또는 식별자)
    - **B열**: instagram_link (Instagram 포스트 URL)
    
    ### 예시:
    | name | instagram_link |
    |------|----------------|
    | 포스트1 | https://www.instagram.com/p/ABC123/ |
    | 포스트2 | https://www.instagram.com/p/DEF456/ |
    | (빈 셀) | (빈 셀) |
    | 포스트4 | https://www.instagram.com/p/GHI789/ |
    
    ### 특징
    - **빈 셀 자동 처리**: 빈 셀이 있어도 자동으로 건너뛰고 유효한 데이터만 크롤링합니다
    - **유효성 검사**: Instagram URL이 아닌 경우 자동으로 제외됩니다
    - **에러 처리**: 개별 포스트에서 에러가 발생해도 전체 작업이 중단되지 않습니다
    - **데이터베이스 저장**: 모든 결과가 자동으로 데이터베이스에 저장됩니다
    
    ### 주의사항
    - 각 포스트 크롤링 후 30-60초의 랜덤 쿨다운 시간이 있습니다
    - 에러가 발생해도 다음 포스트로 계속 진행됩니다
    - Instagram의 정책을 준수하여 사용하세요
    """)
    
    return {"action": "none"}

def render_crawl_history():
    """크롤링 히스토리 표시"""
    st.subheader("📚 크롤링 히스토리")
    
    # 사용자의 크롤링 결과 목록 조회
    results = db_manager.get_user_crawl_results(limit=50)
    
    if results:
        # 데이터프레임으로 변환
        df = pd.DataFrame(results)
        
        # 컬럼명 한글화
        if not df.empty:
            df_display = df[['post_name', 'post_url', 'likes', 'comments', 'status', 'created_at']].copy()
            df_display.columns = ['포스트명', 'URL', '좋아요', '댓글', '상태', '생성일']
            df_display['생성일'] = pd.to_datetime(df_display['생성일']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(df_display, use_container_width=True)
            
            # 통계 표시
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 포스트", len(df))
            with col2:
                success_count = len(df[df['status'] == 'success'])
                st.metric("성공한 포스트", success_count)
            with col3:
                total_likes = df[df['status'] == 'success']['likes'].sum()
                st.metric("총 좋아요", f"{total_likes:,}")
    else:
        st.info("아직 크롤링한 포스트가 없습니다.")
