import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..instagram_crawler import InstagramCrawler
from ..db.database import db_manager
from ..db.models import Campaign, Influencer, CampaignInfluencer, CampaignInfluencerParticipation, PerformanceMetric, InstagramCrawlResult
from ..supabase.auth import supabase_auth

def check_database_for_influencer(platform: str, sns_id: str) -> Dict[str, Any]:
    """데이터베이스에서 인플루언서 정보 확인"""
    try:
        # SNS ID에서 @ 제거
        clean_sns_id = sns_id.replace('@', '') if sns_id else ''
        
        # 데이터베이스에서 인플루언서 정보 조회
        result = db_manager.get_influencer_info(platform, clean_sns_id)
        
        if result["success"] and result["exists"]:
            return {
                "success": True,
                "exists": True,
                "data": result["data"],
                "message": f"✅ 데이터베이스에서 인플루언서를 찾았습니다: {result['data']['influencer_name'] or clean_sns_id}"
            }
        else:
            return {
                "success": True,
                "exists": False,
                "data": None,
                "message": "❌ 데이터베이스에 해당 인플루언서가 없습니다."
            }
    except Exception as e:
        return {
            "success": False,
            "exists": False,
            "data": None,
            "message": f"❌ DB 확인 중 오류가 발생했습니다: {str(e)}"
        }

def perform_crawling(platform: str, url: str, sns_id: str, debug_mode: bool, save_to_db: bool) -> Dict[str, Any]:
    """실제 크롤링 수행"""
    try:
        crawler = InstagramCrawler()
        
        # URL이 없으면 SNS ID로 URL 생성
        if not url and sns_id:
            if platform == "instagram":
                url = f"https://www.instagram.com/{sns_id.replace('@', '')}/"
            elif platform == "youtube":
                return {
                    "success": False,
                    "message": "YouTube는 아직 지원하지 않습니다.",
                    "data": None
                }
            elif platform == "tiktok":
                return {
                    "success": False,
                    "message": "TikTok은 아직 지원하지 않습니다.",
                    "data": None
                }
            elif platform == "twitter":
                return {
                    "success": False,
                    "message": "Twitter는 아직 지원하지 않습니다.",
                    "data": None
                }
        
        # 크롤링 실행 (현재는 Instagram만 지원)
        if platform == "instagram":
            # SNS ID에서 @ 제거
            clean_sns_id = sns_id.replace('@', '') if sns_id else url.split('/')[-2] if url else ''
            
            # Instagram 프로필 크롤링
            result = crawler.crawl_instagram_profile(url, debug_mode)
            
            if result['status'] == 'success':
                # 데이터베이스에 저장 또는 업데이트
                if save_to_db:
                    # 기존 인플루언서 확인
                    existing_influencer = db_manager.check_influencer_exists(platform, clean_sns_id)
                    
                    # 로그인 상태 확인
                    is_logged_in = supabase_auth.is_authenticated()
                    
                    if existing_influencer:
                        # 기존 인플루언서 업데이트
                        update_result = db_manager.update_influencer_data(
                            existing_influencer['id'], 
                            result
                        )
                        if update_result["success"]:
                            db_message = "✅ 인플루언서 데이터가 업데이트되었습니다."
                        else:
                            db_message = f"❌ 업데이트 실패: {update_result['message']}"
                        
                        # 원시 데이터 저장 (기존 인플루언서)
                        if result.get('page_source') and result.get('debug_info'):
                            raw_save_result = db_manager.save_crawl_raw_data(
                                existing_influencer['id'],
                                platform,
                                clean_sns_id,
                                result['page_source'],
                                result.get('raw_profile_data', result),
                                result.get('debug_info', {})
                            )
                            if raw_save_result["success"]:
                                db_message += " 📄 원시 데이터 저장 완료"
                            else:
                                db_message += f" ⚠️ 원시 데이터 저장 실패: {raw_save_result['message']}"
                    else:
                        # 새 인플루언서 생성
                        create_result = db_manager.create_influencer_from_crawl(
                            platform, 
                            clean_sns_id, 
                            result
                        )
                        if create_result["success"]:
                            db_message = "✅ 새로운 인플루언서가 데이터베이스에 저장되었습니다."
                            
                            # 원시 데이터 저장 (새 인플루언서)
                            if result.get('page_source') and result.get('debug_info') and create_result.get('data'):
                                new_influencer_id = create_result['data'][0]['id'] if create_result['data'] else None
                                if new_influencer_id:
                                    raw_save_result = db_manager.save_crawl_raw_data(
                                        new_influencer_id,
                                        platform,
                                        clean_sns_id,
                                        result['page_source'],
                                        result.get('raw_profile_data', result),
                                        result.get('debug_info', {})
                                    )
                                    if raw_save_result["success"]:
                                        db_message += " 📄 원시 데이터 저장 완료"
                                    else:
                                        db_message += f" ⚠️ 원시 데이터 저장 실패: {raw_save_result['message']}"
                        else:
                            db_message = f"❌ 저장 실패: {create_result['message']}"
                else:
                    db_message = "💾 데이터베이스 저장을 건너뛰었습니다."
                
                crawler.close_driver()
                
                return {
                    "success": True,
                    "message": "크롤링이 완료되었습니다!",
                    "data": {
                        "result": result,
                        "clean_sns_id": clean_sns_id,
                        "db_message": db_message
                    }
                }
            else:
                crawler.close_driver()
                return {
                    "success": False,
                    "message": f"크롤링 실패: {result.get('error', '알 수 없는 오류')}",
                    "data": None
                }
        else:
            crawler.close_driver()
            return {
                "success": False,
                "message": f"{platform.title()} 크롤링은 아직 지원되지 않습니다. Instagram만 지원됩니다.",
                "data": None
            }
            
    except Exception as e:
        if 'crawler' in locals():
            crawler.close_driver()
        return {
            "success": False,
            "message": f"크롤링 중 오류가 발생했습니다: {str(e)}",
            "data": None
        }

def render_single_url_crawl():
    """단일 URL 크롤링 컴포넌트"""
    st.subheader("🔍 단일 URL 크롤링")
    st.markdown("플랫폼과 SNS ID 또는 URL을 입력하여 해당 계정의 내용을 크롤링합니다.")
    
    # 플랫폼 선택
    platform = st.selectbox(
        "플랫폼 선택",
        ["instagram", "youtube", "tiktok", "twitter"],
        key="single_crawl_platform",
        format_func=lambda x: {
            "instagram": "📸 Instagram",
            "youtube": "📺 YouTube", 
            "tiktok": "🎵 TikTok",
            "twitter": "🐦 Twitter"
        }[x]
    )
    
    # 입력 방식 선택
    input_type = st.radio(
        "입력 방식",
        ["SNS ID", "URL"],
        horizontal=True
    )
    
    if input_type == "SNS ID":
        sns_id = st.text_input(
            f"{platform.title()} ID",
            placeholder=f"@{platform}_username 또는 username",
            help="사용자명 또는 @를 포함한 전체 ID를 입력하세요"
        )
        url = None
    else:
        url = st.text_input(
            f"{platform.title()} URL",
            placeholder=f"https://www.{platform}.com/...",
            help=f"{platform.title()} 프로필 또는 포스트 URL을 입력하세요"
        )
        sns_id = None
    
    # 크롤링 옵션
    col1, col2 = st.columns(2)
    with col1:
        debug_mode = st.checkbox("🔍 디버그 모드", help="페이지의 HTML 요소들을 확인할 수 있습니다", key="single_crawl_debug_mode")
    with col2:
        save_to_db = st.checkbox("💾 데이터베이스 저장", value=True, help="크롤링 결과를 데이터베이스에 저장합니다", key="single_crawl_save_to_db")
    
    # DB 확인 상태 초기화
    if 'db_checked' not in st.session_state:
        st.session_state.db_checked = False
    if 'db_result' not in st.session_state:
        st.session_state.db_result = None
    if 'last_input' not in st.session_state:
        st.session_state.last_input = None
    
    # 입력값이 변경되면 DB 확인 상태 초기화
    current_input = f"{platform}_{sns_id}_{url}"
    if st.session_state.last_input != current_input:
        st.session_state.db_checked = False
        st.session_state.db_result = None
        st.session_state.last_input = current_input
    
    # 두 단계 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 DB 확인", type="secondary"):
            if not sns_id and not url:
                st.error("SNS ID 또는 URL을 입력해주세요!")
                return
            
            # SNS ID 추출
            if sns_id:
                clean_sns_id = sns_id.replace('@', '')
            else:
                clean_sns_id = url.split('/')[-2] if url else ''
            
            with st.spinner(""):
                db_result = check_database_for_influencer(platform, clean_sns_id)
                
                # 세션 상태에 저장
                st.session_state.db_checked = True
                st.session_state.db_result = db_result
                st.session_state.clean_sns_id = clean_sns_id
                
                if db_result["success"]:
                    if db_result["exists"]:
                        st.success(db_result["message"])
                        
                        # DB에서 가져온 정보 표시
                        data = db_result["data"]
                        st.subheader("📊 데이터베이스 정보")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("👤 이름", data.get("influencer_name", "N/A"))
                        with col2:
                            st.metric("👥 팔로워 수", f"{data.get('followers_count', 0):,}")
                        with col3:
                            st.metric("📝 게시물 수", f"{data.get('post_count', 0):,}")
                        
                        if data.get("profile_url"):
                            st.image(data["profile_url"], width=150, caption="프로필 이미지")
                        
                        st.info(f"📅 등록일: {data.get('created_at', 'N/A')[:10] if data.get('created_at') else 'N/A'}")
                    else:
                        st.info(db_result["message"])
                        
                        # 디버깅 정보 표시
                        if "debug_info" in db_result:
                            with st.expander("🔍 디버깅 정보", expanded=False):
                                debug_info = db_result["debug_info"]
                                st.json(debug_info)
                                
                                # 모든 인플루언서 목록 표시
                                if "all_influencers" in debug_info:
                                    st.write("**현재 DB에 있는 모든 인플루언서:**")
                                    for inf in debug_info["all_influencers"]:
                                        st.write(f"- {inf.get('sns_id', 'N/A')} ({inf.get('platform', 'N/A')}) - {inf.get('influencer_name', 'N/A')}")
                else:
                    st.error(db_result["message"])
                    
                    # 에러 시 디버깅 정보 표시
                    if "debug_info" in db_result:
                        with st.expander("🔍 에러 디버깅 정보", expanded=True):
                            st.json(db_result["debug_info"])
    
    with col2:
        # DB 확인이 완료된 경우에만 크롤링 시작 버튼 활성화
        if st.session_state.db_checked:
            if st.button("🚀 크롤링 시작", type="primary", key="single_url_crawl_start"):
                if not sns_id and not url:
                    st.error("SNS ID 또는 URL을 입력해주세요!")
                    return
                
                with st.spinner(""):
                    crawl_result = perform_crawling(platform, url, sns_id, debug_mode, save_to_db)
                    
                    if crawl_result["success"]:
                        st.success(crawl_result["message"])
                        
                        result = crawl_result["data"]["result"]
                        clean_sns_id = crawl_result["data"]["clean_sns_id"]
                        db_message = crawl_result["data"]["db_message"]
                        
                        # 프로필 이미지 표시
                        if result.get('profile_image_url'):
                            st.image(result['profile_image_url'], width=150, caption="프로필 이미지")
                        
                        # 결과를 카드 형태로 표시
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                label="👤 이름",
                                value=result.get('influencer_name', 'N/A'),
                                help="인플루언서 이름"
                            )
                        
                        with col2:
                            st.metric(
                                label="📝 게시물 수",
                                value=f"{result.get('post_count', 0):,}",
                                help="총 게시물 수"
                            )
                        
                        with col3:
                            st.metric(
                                label="👥 팔로워 수",
                                value=f"{result.get('followers_count', 0):,}",
                                help="팔로워 수"
                            )
                        
                        with col4:
                            st.metric(
                                label="📊 팔로잉 수",
                                value="N/A",
                                help="팔로잉 수 (추출 예정)"
                            )
                        
                        # 프로필 텍스트 표시
                        if result.get('profile_text'):
                            st.subheader("📝 프로필 내용")
                            st.text_area("", value=result['profile_text'], height=100, disabled=True)
                        
                        # 데이터베이스 저장 결과 표시
                        if save_to_db:
                            st.info(db_message)
                        
                        # 데이터프레임으로 표시
                        df = pd.DataFrame([{
                            '플랫폼': platform.title(),
                            'SNS ID': clean_sns_id,
                            '이름': result.get('influencer_name', 'N/A'),
                            '게시물 수': result.get('post_count', 0),
                            '팔로워 수': result.get('followers_count', 0),
                            '프로필 URL': result.get('profile_image_url', 'N/A'),
                            '프로필 내용': result.get('profile_text', 'N/A')
                        }])
                        
                        st.subheader("📊 결과 요약")
                        st.dataframe(df, use_container_width=True)
                        
                        # CSV 다운로드 버튼
                        csv = df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 CSV 다운로드",
                            data=csv,
                            file_name=f"{platform}_profile_crawl_result.csv",
                            mime="text/csv"
                        )
                    else:
                        st.error(crawl_result["message"])
        else:
            # DB 확인이 완료되지 않은 경우 비활성화된 버튼 표시
            st.button("🚀 크롤링 시작", disabled=True, help="먼저 'DB 확인' 버튼을 클릭해주세요", key="single_url_crawl_start_disabled")
    
    # DB 확인 결과가 있으면 표시
    if st.session_state.db_checked and st.session_state.db_result:
        st.info("✅ DB 확인이 완료되었습니다. 이제 크롤링을 시작할 수 있습니다.")

def render_batch_url_crawl():
    """복수 URL 크롤링 컴포넌트"""
    st.subheader("📊 복수 URL 크롤링")
    st.markdown("데이터베이스에서 업데이트할 목록을 선택하여 일괄 크롤링을 수행합니다.")
    
    # 데이터베이스에서 크롤링할 목록 조회 (캐싱 적용)
    st.subheader("📋 크롤링 대상 선택")
    
    # 캐시 키 생성
    cache_key = "influencers_data"
    
    # 세션 상태에서 캐시된 데이터 확인
    if cache_key not in st.session_state:
        with st.spinner("인플루언서 데이터를 불러오는 중..."):
            st.session_state[cache_key] = db_manager.get_influencers()
    
    # 캐시된 데이터 사용
    all_influencers_data = st.session_state[cache_key]
    
    # 데이터 새로고침 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📊 총 {len(all_influencers_data)}명의 인플루언서 데이터가 캐시되어 있습니다.")
    with col2:
        if st.button("🔄 새로고침", help="데이터베이스에서 최신 데이터를 다시 불러옵니다"):
            with st.spinner("데이터를 새로고침하는 중..."):
                st.session_state[cache_key] = db_manager.get_influencers()
            st.success("데이터가 새로고침되었습니다!")
            st.rerun()
    
    # 플랫폼별 필터
    platform_filter = st.selectbox(
        "플랫폼 필터",
        ["전체", "instagram", "youtube", "tiktok", "twitter"],
        key="batch_crawl_platform_filter",
        format_func=lambda x: {
            "전체": "🌐 전체",
            "instagram": "📸 Instagram",
            "youtube": "📺 YouTube",
            "tiktok": "🎵 TikTok", 
            "twitter": "🐦 Twitter"
        }[x]
    )
    
    # 마지막 업데이트 기반 필터
    st.subheader("🕒 업데이트 기반 필터")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        update_filter_type = st.selectbox(
            "업데이트 필터 타입",
            ["전체", "마지막 업데이트 이후", "마지막 업데이트 이전"],
            key="update_filter_type",
            help="마지막 업데이트 시간을 기준으로 필터링합니다"
        )
    
    with col2:
        if update_filter_type != "전체":
            # 마지막 업데이트 날짜 선택
            default_date = datetime.now() - timedelta(days=7)  # 기본값: 7일 전
            
            update_date = st.date_input(
                "기준 날짜",
                value=default_date,
                key="update_filter_date",
                help="이 날짜를 기준으로 필터링합니다"
            )
        else:
            update_date = None
    
    with col3:
        first_crawled_only = st.checkbox(
            "🆕 첫 크롤링만",
            key="first_crawled_filter",
            help="아직 크롤링되지 않은 인플루언서만 선택합니다 (first_crawled = FALSE)"
        )
    
    # 캐시된 데이터에서 필터링 (DB 호출 없이)
    all_influencers_total = [inf for inf in all_influencers_data 
                           if platform_filter == "전체" or inf['platform'] == platform_filter]
    
    # 필터링된 인플루언서 목록 조회 (실제 표시할 목록)
    filtered_influencers = db_manager.get_influencers_with_update_filter(
        platform=platform_filter if platform_filter != "전체" else None,
        update_filter_type=update_filter_type,
        update_date=update_date,
        first_crawled_only=first_crawled_only
    )
    
    if not filtered_influencers:
        st.info("크롤링할 인플루언서가 없습니다. 먼저 인플루언서를 등록해주세요.")
        return
    
    # 인플루언서 선택 옵션 생성
    filtered_influencer_options = {f"{inf.get('influencer_name') or inf['sns_id']} ({inf['platform']})": inf['id'] for inf in filtered_influencers}
    
    # 필터링 결과 표시
    if first_crawled_only:
        st.info(f"📊 {len(filtered_influencers)}개 인플루언서가 표시됩니다 (첫 크롤링 대상)")
    else:
        st.info(f"📊 {len(filtered_influencers)}개 인플루언서가 표시됩니다")
    
    # 모두선택 옵션 추가
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_influencers = st.multiselect(
            "크롤링할 인플루언서 선택",
            options=list(filtered_influencer_options.keys()),
            help="여러 인플루언서를 선택할 수 있습니다"
        )
    
    with col2:
        if st.button("✅ 모두선택", help="표시된 모든 인플루언서를 선택합니다", key="select_filtered_influencers"):
            st.session_state.selected_filtered_influencers = True
            st.rerun()
        
        if st.button("❌ 모두해제", help="모든 선택을 해제합니다", key="clear_all_selections"):
            st.session_state.selected_filtered_influencers = False
            st.session_state.selected_all_influencers = False
            st.rerun()
    
    with col3:
        if st.button("🌐 전체선택", help="전체 인플루언서를 선택합니다 (필터 무시)", key="select_all_influencers"):
            st.session_state.selected_all_influencers = True
            st.session_state.selected_filtered_influencers = False
            st.rerun()
    
    # 선택 상태 처리
    if hasattr(st.session_state, 'selected_filtered_influencers') and st.session_state.selected_filtered_influencers:
        selected_influencers = list(filtered_influencer_options.keys())
    elif hasattr(st.session_state, 'selected_all_influencers') and st.session_state.selected_all_influencers:
        # 전체 인플루언서 선택 시 전체 목록을 다시 조회
        all_influencer_options = {f"{inf.get('influencer_name') or inf['sns_id']} ({inf['platform']})": inf['id'] for inf in all_influencers_total}
        selected_influencers = list(all_influencer_options.keys())
        st.warning("⚠️ 전체 인플루언서가 선택되었습니다. 필터 조건을 무시하고 모든 인플루언서를 크롤링합니다.")
    
    if not selected_influencers:
        st.warning("크롤링할 인플루언서를 선택해주세요.")
        return
    
    # 크롤링 옵션
    col1, col2 = st.columns(2)
    with col1:
        debug_mode = st.checkbox("🔍 디버그 모드", help="페이지의 HTML 요소들을 확인할 수 있습니다", key="batch_crawl_debug_mode")
    with col2:
        session_name = st.text_input("세션 이름", value=f"Batch Crawl - {len(selected_influencers)} influencers", key="batch_crawl_session_name")
    
    if st.button("🚀 일괄 크롤링 시작", type="primary", key="batch_crawl_start_influencers"):
        if not selected_influencers:
            st.error("크롤링할 인플루언서를 선택해주세요.")
            return
        
        # 크롤링 세션 생성
        session_result = db_manager.create_instagram_crawl_session(session_name, len(selected_influencers))
        session_id = None
        if session_result["success"]:
            session_id = session_result["data"][0]["id"]
            st.info(f"크롤링 세션이 생성되었습니다. (ID: {session_id})")
        
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
                results = []
                
                # 사용할 인플루언서 데이터 결정
                if hasattr(st.session_state, 'selected_all_influencers') and st.session_state.selected_all_influencers:
                    # 전체 인플루언서 선택된 경우
                    influencers_to_use = all_influencers_total
                    influencer_options_to_use = all_influencer_options
                else:
                    # 필터링된 인플루언서 선택된 경우
                    influencers_to_use = filtered_influencers
                    influencer_options_to_use = filtered_influencer_options
                
                for i, influencer_name in enumerate(selected_influencers):
                    influencer_id = influencer_options_to_use[influencer_name]
                    influencer = next(inf for inf in influencers_to_use if inf['id'] == influencer_id)
                    
                    # 안전한 진행률 업데이트
                    try:
                        from src.instagram_crawler import safe_streamlit_update
                        progress = min(max(i / len(selected_influencers), 0.0), 1.0)
                        safe_streamlit_update(
                            progress_bar, 
                            progress_text, 
                            status_text, 
                            progress, 
                            i, 
                            len(selected_influencers), 
                            f"크롤링 중: {influencer.get('influencer_name') or influencer['sns_id']}"
                        )
                    except Exception as e:
                        # 진행률 업데이트 실패 시 조용히 무시
                        pass
                    
                    try:
                        # 단일 URL 크롤링 자동화 - 인플루언서 프로필 크롤링
                        if influencer['platform'] == 'instagram':
                            # Instagram 프로필 URL 생성
                            sns_id_clean = influencer['sns_id'].replace('@', '')
                            url = f"https://www.instagram.com/{sns_id_clean}/"
                            
                            # 인플루언서 프로필 크롤링 (단일 URL 크롤링 자동화)
                            result = crawler.crawl_instagram_profile(url, debug_mode)
                            
                            # 크롤링 결과를 데이터베이스에 저장
                            if result['status'] == 'success':
                                # 인플루언서 데이터 업데이트
                                update_result = db_manager.update_influencer_data(influencer_id, result)
                                if update_result["success"]:
                                    st.success(f"✅ {influencer.get('influencer_name') or influencer['sns_id']} 데이터 업데이트 완료")
                                
                                # 크롤링 원시 데이터 저장
                                raw_data_result = db_manager.save_crawl_raw_data(
                                    influencer_id, 
                                    influencer['platform'], 
                                    influencer['sns_id'],
                                    result.get('page_source', ''),
                                    result,
                                    result.get('debug_info', {})
                                )
                            
                        else:
                            result = {
                                'status': 'error',
                                'error': f"{influencer['platform']} 크롤링은 아직 지원되지 않습니다."
                            }
                        
                        results.append({
                            'name': influencer.get('influencer_name') or influencer['sns_id'],
                            'platform': influencer['platform'],
                            'sns_id': influencer['sns_id'],
                            'url': url if influencer['platform'] == 'instagram' else 'N/A',
                            'followers': result.get('followers_count', 0),
                            'posts': result.get('post_count', 0),
                            'status': result['status'],
                            'error': result.get('error', ''),
                            'updated_at': result.get('updated_at', '')
                        })
                        
                    except Exception as e:
                        results.append({
                            'name': influencer.get('influencer_name') or influencer['sns_id'],
                            'platform': influencer['platform'],
                            'sns_id': influencer['sns_id'],
                            'url': 'N/A',
                            'followers': 0,
                            'posts': 0,
                            'status': 'error',
                            'error': str(e),
                            'updated_at': ''
                        })
                
                crawler.close_driver()
                
                # 안전한 완료 진행률 업데이트
                try:
                    from src.instagram_crawler import safe_streamlit_update
                    safe_streamlit_update(
                        progress_bar, 
                        progress_text, 
                        status_text, 
                        1.0, 
                        len(selected_influencers), 
                        len(selected_influencers), 
                        "크롤링 완료"
                    )
                except Exception as e:
                    # 진행률 업데이트 실패 시 조용히 무시
                    pass
        
        # 결과를 데이터베이스에 저장 (인플루언서 프로필 크롤링 결과)
        successful_crawls = 0
        failed_crawls = 0
        
        for result in results:
            if result['status'] == 'success':
                # 인플루언서 프로필 크롤링 결과를 세션에 기록
                crawl_result = InstagramCrawlResult(
                    session_id=session_id,
                    post_name=f"Profile - {result['name']}",
                    post_url=result['url'],
                    likes=0,  # 프로필 크롤링에서는 좋아요 수가 없음
                    comments=0,  # 프로필 크롤링에서는 댓글 수가 없음
                    status=result['status']
                )
                
                save_result = db_manager.save_instagram_crawl_result(crawl_result)
                if save_result["success"]:
                    successful_crawls += 1
            else:
                failed_crawls += 1
        
        # 세션 업데이트
        if session_id:
            db_manager.update_instagram_crawl_session(session_id, successful_crawls, failed_crawls, "completed")
        
        # 결과 표시
        st.success("일괄 크롤링이 완료되었습니다!")
        
        # 결과 데이터프레임 생성
        results_df = pd.DataFrame(results)
        
        # 통계 표시
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 인플루언서", len(results_df))
        with col2:
            success_count = len(results_df[results_df['status'] == 'success'])
            st.metric("성공", success_count)
        with col3:
            error_count = len(results_df[results_df['status'] == 'error'])
            st.metric("실패", error_count)
        with col4:
            total_followers = results_df[results_df['status'] == 'success']['followers'].sum()
            st.metric("총 팔로워", f"{total_followers:,}")
        
        # 결과 테이블 표시 (필요한 컬럼만)
        st.subheader("📊 크롤링 결과")
        display_df = results_df[['name', 'platform', 'sns_id', 'followers', 'posts', 'status', 'error']].copy()
        display_df.columns = ['인플루언서명', '플랫폼', 'SNS ID', '팔로워 수', '게시물 수', '상태', '오류']
        st.dataframe(display_df, use_container_width=True)
        
        # CSV 다운로드
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 결과 CSV 다운로드",
            data=csv,
            file_name="influencer_batch_crawl_results.csv",
            mime="text/csv"
        )
        
        # 에러가 있는 경우 상세 표시
        error_results = results_df[results_df['status'] == 'error']
        if len(error_results) > 0:
            st.subheader("⚠️ 에러 상세 정보")
            error_display = error_results[['name', 'platform', 'sns_id', 'error']].copy()
            error_display.columns = ['인플루언서명', '플랫폼', 'SNS ID', '오류 메시지']
            st.dataframe(error_display, use_container_width=True)

def render_campaign_management():
    """캠페인 관리 컴포넌트"""
    st.subheader("📋 캠페인 관리")
    st.markdown("시딩, 홍보, 판매 캠페인을 생성하고 참여 인플루언서를 관리합니다.")
    
    # 탭으로 캠페인 관리와 참여 인플루언서 관리 구분
    tab1, tab2 = st.tabs(["📁 캠페인 관리", "👥 참여 인플루언서 관리"])
    
    with tab1:
        render_campaign_tab()
    
    with tab2:
        render_campaign_participation_tab()

def render_campaign_tab():
    """캠페인 탭"""
    st.subheader("📁 캠페인 관리")
    
    # 새 캠페인 생성
    with st.expander("➕ 새 캠페인 생성", expanded=True):
        with st.form("create_campaign_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                campaign_name = st.text_input("캠페인 이름", placeholder="예: 2024 봄 시즌 시딩")
                campaign_type = st.selectbox(
                    "캠페인 유형",
                    ["seeding", "promotion", "sales"],
                    key="create_campaign_type",
                    format_func=lambda x: {
                        "seeding": "🌱 시딩",
                        "promotion": "📢 홍보", 
                        "sales": "💰 판매"
                    }[x]
                )
                start_date = st.date_input("캠페인 시작날짜", value=datetime.now().date())
            
            with col2:
                campaign_description = st.text_area("캠페인 설명", placeholder="캠페인에 대한 상세 설명을 입력하세요")
                status = st.selectbox(
                    "캠페인 상태",
                    ["planned", "active", "paused", "completed", "canceled"],
                    key="create_campaign_status",
                    format_func=lambda x: {
                        "planned": "📅 계획됨",
                        "active": "🟢 진행중",
                        "paused": "⏸️ 일시정지",
                        "completed": "✅ 완료",
                        "canceled": "❌ 취소"
                    }[x]
                )
                end_date = st.date_input("캠페인 종료일", value=None)
            
            # 추가 필드들
            campaign_instructions = st.text_area("캠페인 지시사항", placeholder="인플루언서에게 전달할 구체적인 지시사항을 입력하세요")
            
            # 태그 입력
            tags_input = st.text_input("태그", placeholder="태그를 쉼표로 구분하여 입력하세요 (예: 봄시즌, 뷰티, 신제품)")
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else None
            
            if st.form_submit_button("캠페인 생성", type="primary"):
                if not campaign_name:
                    st.error("캠페인 이름을 입력해주세요.")
                elif not start_date:
                    st.error("캠페인 시작날짜를 선택해주세요.")
                elif end_date and end_date < start_date:
                    st.error("종료일은 시작일보다 늦어야 합니다.")
                else:
                    campaign = Campaign(
                        campaign_name=campaign_name,
                        campaign_description=campaign_description,
                        campaign_type=campaign_type,
                        start_date=start_date,
                        end_date=end_date,
                        status=status,
                        campaign_instructions=campaign_instructions,
                        tags=tags
                    )
                    
                    result = db_manager.create_campaign(campaign)
                    if result["success"]:
                        st.success("캠페인이 생성되었습니다!")
                        st.rerun()
                    else:
                        st.error(f"캠페인 생성 실패: {result['message']}")
    
    # 기존 캠페인 목록
    st.subheader("📋 캠페인 목록")
    
    # 캠페인 목록
    
    # 필터링 옵션
    st.markdown("### 🔍 필터링 옵션")
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    
    with filter_col1:
        # 캠페인 유형 필터
        campaign_type_filter = st.selectbox(
            "캠페인 유형",
            options=["전체", "seeding", "promotion", "sales"],
            index=0 if "campaign_type_filter" not in st.session_state else ["전체", "seeding", "promotion", "sales"].index(st.session_state.get("campaign_type_filter", "전체")),
            key="campaign_type_filter",
            help="캠페인 유형으로 필터링합니다"
        )
    
    with filter_col2:
        # 캠페인 상태 필터
        campaign_status_filter = st.selectbox(
            "캠페인 상태",
            options=["전체", "planned", "active", "paused", "completed", "canceled"],
            index=0 if "campaign_status_filter" not in st.session_state else ["전체", "planned", "active", "paused", "completed", "canceled"].index(st.session_state.get("campaign_status_filter", "전체")),
            key="campaign_status_filter",
            help="캠페인 상태로 필터링합니다"
        )
    
    with filter_col3:
        st.markdown("")  # 공간 확보
        st.markdown("")  # 공간 확보
        if st.button("🔄 새로고침", key="refresh_campaigns", help="캠페인 목록을 새로 불러옵니다"):
            st.rerun()
    
    # 모든 캠페인 조회 (생성자와 상관없이)
    campaigns = db_manager.get_campaigns()
    
    # 필터링 적용
    filtered_campaigns = campaigns
    if campaign_type_filter != "전체":
        filtered_campaigns = [c for c in filtered_campaigns if c['campaign_type'] == campaign_type_filter]
    
    if campaign_status_filter != "전체":
        filtered_campaigns = [c for c in filtered_campaigns if c['status'] == campaign_status_filter]
    
    if filtered_campaigns:
        # 필터링 결과 표시
        if len(filtered_campaigns) != len(campaigns):
            st.info(f"🔍 필터링 결과: {len(filtered_campaigns)}개 (전체 {len(campaigns)}개 중)")
        else:
            st.success(f"✅ {len(filtered_campaigns)}개의 캠페인을 찾았습니다.")
        
        for i, campaign in enumerate(filtered_campaigns):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{campaign['campaign_name']}**")
                    st.caption(f"유형: {campaign['campaign_type']} | 상태: {campaign['status']}")
                    st.caption(f"기간: {campaign['start_date']} ~ {campaign['end_date'] or '미정'}")
                    if campaign['campaign_description']:
                        st.caption(campaign['campaign_description'])
                    if campaign.get('campaign_instructions'):
                        st.caption(f"📋 지시사항: {campaign['campaign_instructions']}")
                    if campaign.get('tags') and len(campaign['tags']) > 0:
                        tags_display = ", ".join(campaign['tags'])
                        st.caption(f"🏷️ 태그: {tags_display}")
                
                with col2:
                    if st.button("✏️ 수정", key=f"edit_{campaign['id']}_{i}", help="캠페인 정보를 수정합니다"):
                        st.session_state[f"editing_campaign_{campaign['id']}"] = True
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ 삭제", key=f"delete_{campaign['id']}_{i}", help="캠페인을 삭제합니다"):
                        result = db_manager.delete_campaign(campaign['id'])
                        if result["success"]:
                            st.success("캠페인이 삭제되었습니다!")
                            st.rerun()
                        else:
                            st.error(f"삭제 실패: {result['message']}")
                
                st.divider()
                
                # 캠페인 수정 폼 (수정 버튼이 클릭된 경우)
                if st.session_state.get(f"editing_campaign_{campaign['id']}", False):
                    render_campaign_edit_form(campaign)
    else:
        if campaigns:
            st.warning("🔍 선택한 필터 조건에 맞는 캠페인이 없습니다.")
        else:
            st.info("생성된 캠페인이 없습니다.")

def render_campaign_edit_form(campaign):
    """캠페인 수정 폼"""
    st.markdown("---")
    st.subheader(f"✏️ 캠페인 수정: {campaign['campaign_name']}")
    
    with st.form(f"edit_campaign_form_{campaign['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            # 기존 값으로 폼 초기화
            campaign_name = st.text_input(
                "캠페인 이름", 
                value=campaign['campaign_name'],
                key=f"edit_name_{campaign['id']}"
            )
            
            campaign_type = st.selectbox(
                "캠페인 유형",
                ["seeding", "promotion", "sales"],
                index=["seeding", "promotion", "sales"].index(campaign['campaign_type']),
                key=f"edit_type_{campaign['id']}",
                format_func=lambda x: {
                    "seeding": "🌱 시딩",
                    "promotion": "📢 홍보", 
                    "sales": "💰 판매"
                }[x]
            )
            
            # 날짜 변환
            start_date = st.date_input(
                "캠페인 시작날짜", 
                value=datetime.strptime(campaign['start_date'], '%Y-%m-%d').date(),
                key=f"edit_start_{campaign['id']}"
            )
        
        with col2:
            campaign_description = st.text_area(
                "캠페인 설명", 
                value=campaign.get('campaign_description', ''),
                key=f"edit_desc_{campaign['id']}"
            )
            
            status = st.selectbox(
                "캠페인 상태",
                ["planned", "active", "paused", "completed", "canceled"],
                index=["planned", "active", "paused", "completed", "canceled"].index(campaign['status']),
                key=f"edit_status_{campaign['id']}",
                format_func=lambda x: {
                    "planned": "📅 계획됨",
                    "active": "🟢 진행중",
                    "paused": "⏸️ 일시정지",
                    "completed": "✅ 완료",
                    "canceled": "❌ 취소"
                }[x]
            )
            
            # 종료일 처리
            end_date_value = None
            if campaign.get('end_date'):
                end_date_value = datetime.strptime(campaign['end_date'], '%Y-%m-%d').date()
            
            end_date = st.date_input(
                "캠페인 종료일", 
                value=end_date_value,
                key=f"edit_end_{campaign['id']}"
            )
        
        # 추가 필드들
        campaign_instructions = st.text_area(
            "캠페인 지시사항", 
            value=campaign.get('campaign_instructions', ''),
            key=f"edit_instructions_{campaign['id']}"
        )
        
        # 태그 처리
        tags_input = st.text_input(
            "태그", 
            value=", ".join(campaign.get('tags', [])) if campaign.get('tags') else "",
            key=f"edit_tags_{campaign['id']}",
            placeholder="태그를 쉼표로 구분하여 입력하세요 (예: 봄시즌, 뷰티, 신제품)"
        )
        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else None
        
        # 버튼들
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.form_submit_button("💾 수정하기", type="primary"):
                if not campaign_name:
                    st.error("캠페인 이름을 입력해주세요.")
                elif not start_date:
                    st.error("캠페인 시작날짜를 선택해주세요.")
                elif end_date and end_date < start_date:
                    st.error("종료일은 시작일보다 늦어야 합니다.")
                else:
                    # 캠페인 데이터 준비
                    update_data = {
                        "campaign_name": campaign_name,
                        "campaign_description": campaign_description,
                        "campaign_type": campaign_type,
                        "start_date": start_date.strftime('%Y-%m-%d'),
                        "end_date": end_date.strftime('%Y-%m-%d') if end_date else None,
                        "status": status,
                        "campaign_instructions": campaign_instructions,
                        "tags": tags
                    }
                    
                    result = db_manager.update_campaign(campaign['id'], update_data)
                    if result["success"]:
                        st.success("캠페인이 수정되었습니다!")
                        # 수정 모드 종료
                        st.session_state[f"editing_campaign_{campaign['id']}"] = False
                        st.rerun()
                    else:
                        st.error(f"캠페인 수정 실패: {result['message']}")
        
        with col2:
            if st.form_submit_button("❌ 취소"):
                # 수정 모드 종료
                st.session_state[f"editing_campaign_{campaign['id']}"] = False
                st.rerun()
    
    st.markdown("---")

def render_add_influencer_workflow(campaign_id):
    """인플루언서 추가 워크플로우 (검색 → 정보 확인 → 추가)"""
    st.subheader("➕ 인플루언서 추가")
    
    # 1단계: 인플루언서 검색 (별도 폼)
    st.markdown("### 1️⃣ 인플루언서 검색")
    with st.form("search_influencer_form"):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            platform = st.selectbox(
                "플랫폼",
                ["instagram", "youtube", "tiktok", "twitter"],
                key="search_platform",
                format_func=lambda x: {
                    "instagram": "📸 Instagram",
                    "youtube": "📺 YouTube",
                    "tiktok": "🎵 TikTok",
                    "twitter": "🐦 Twitter"
                }[x]
            )
        
        with col2:
            sns_id = st.text_input("SNS ID", placeholder="@username 또는 username", key="search_sns_id")
        
        search_clicked = st.form_submit_button("🔍 인플루언서 검색", type="primary")
    
    # 검색 결과 처리
    selected_influencer = None
    if search_clicked:
        if not sns_id:
            st.error("SNS ID를 입력해주세요.")
        else:
            # SNS ID에서 @ 제거
            clean_sns_id = sns_id.replace('@', '')
            
            # 인플루언서 검색
            influencer_info = db_manager.get_influencer_info(platform, clean_sns_id)
            
            if influencer_info["success"] and influencer_info["exists"]:
                selected_influencer = influencer_info["data"]
                st.session_state["selected_influencer_for_campaign"] = selected_influencer
                st.success("인플루언서를 찾았습니다!")
                st.rerun()
            else:
                st.error("해당 인플루언서를 찾을 수 없습니다. 먼저 인플루언서를 등록해주세요.")
    
    # 세션에서 선택된 인플루언서 가져오기
    if "selected_influencer_for_campaign" in st.session_state:
        selected_influencer = st.session_state["selected_influencer_for_campaign"]
    
    # 2단계: 검색된 인플루언서 정보 표시
    if selected_influencer:
        st.markdown("### 2️⃣ 인플루언서 정보 확인")
        render_influencer_info_inline(selected_influencer)
        
        # 3단계: 담당자 의견 및 비용 입력 (별도 폼)
        st.markdown("### 3️⃣ 담당자 의견 및 비용 입력")
        with st.form("add_influencer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                manager_comment = st.text_area(
                    "담당자 의견", 
                    placeholder="인플루언서에 대한 담당자 메모나 지시사항을 입력하세요",
                    key="manager_comment_input"
                )
                
                influencer_requests = st.text_area(
                    "인플루언서 요청사항", 
                    placeholder="인플루언서에게 전달할 요청사항을 입력하세요",
                    key="influencer_requests_input"
                )
            
            with col2:
                cost_krw = st.number_input(
                    "비용 (원)", 
                    min_value=0, 
                    value=0, 
                    step=1000,
                    key="cost_input",
                    help="인플루언서에게 지급할 비용을 입력하세요"
                )
                
                sample_status = st.selectbox(
                    "샘플 상태",
                    ["요청", "발송준비", "발송완료", "수령"],
                    key="sample_status_input",
                    help="샘플 발송 상태를 선택하세요"
                )
                
                memo = st.text_area(
                    "메모", 
                    placeholder="추가 메모사항을 입력하세요",
                    key="memo_input"
                )
            
            # 버튼들
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.form_submit_button("✅ 인플루언서 추가", type="primary"):
                    # 디버깅 정보
                    st.write("🔍 디버깅 정보:")
                    st.write(f"- Campaign ID: {campaign_id}")
                    st.write(f"- Influencer ID: {selected_influencer['id']}")
                    st.write(f"- Manager Comment: {manager_comment}")
                    st.write(f"- Cost: {cost_krw}")
                    
                    # 참여 데이터 생성
                    participation = CampaignInfluencerParticipation(
                        campaign_id=campaign_id,
                        influencer_id=selected_influencer["id"],
                        manager_comment=manager_comment,
                        influencer_requests=influencer_requests,
                        memo=memo,
                        sample_status=sample_status,
                        cost_krw=cost_krw
                    )
                    
                    st.write("📝 Participation 객체 생성 완료")
                    
                    result = db_manager.add_influencer_to_campaign(participation)
                    
                    st.write(f"📊 DB 결과: {result}")
                    
                    if result["success"]:
                        st.success("인플루언서가 캠페인에 추가되었습니다!")
                        # 세션 정리
                        if "selected_influencer_for_campaign" in st.session_state:
                            del st.session_state["selected_influencer_for_campaign"]
                        st.rerun()
                    else:
                        st.error(f"추가 실패: {result['message']}")
            
            with col2:
                if st.form_submit_button("❌ 취소"):
                    # 세션 정리
                    if "selected_influencer_for_campaign" in st.session_state:
                        del st.session_state["selected_influencer_for_campaign"]
                    st.rerun()

def render_influencer_info_inline(influencer):
    """인라인 인플루언서 정보 표시 (폼 내에서 사용)"""
    # 정보 카드 형태로 표시
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 프로필 이미지 (가운데 정렬)
        profile_image_url = influencer.get('profile_image_url')
        if profile_image_url and profile_image_url.strip():
            try:
                # CSS를 사용하여 이미지 가운데 정렬
                st.markdown("""
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                    <img src="{}" style="width: 150px; height: 150px; object-fit: cover; border-radius: 50%; border: 2px solid #e0e0e0;">
                </div>
                """.format(profile_image_url), unsafe_allow_html=True)
                st.markdown("<div style='text-align: center; font-size: 0.8em; color: #666;'>프로필 이미지</div>", unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"프로필 이미지를 불러올 수 없습니다: {profile_image_url}")
        else:
            # 프로필 이미지가 없을 때도 가운데 정렬
            st.markdown("""
            <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                <div style="width: 150px; height: 150px; background-color: #f0f0f0; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid #e0e0e0;">
                    <span style="color: #999; font-size: 0.9em;">이미지 없음</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; font-size: 0.8em; color: #666;'>프로필 이미지</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**📱 SNS ID:** `{influencer['sns_id']}`")
        st.markdown(f"**👤 인플루언서 이름:** {influencer.get('influencer_name', 'N/A')}")
        st.markdown(f"**🌐 SNS URL:** {influencer.get('sns_url', 'N/A')}")
        st.markdown(f"**👥 팔로워 수:** {influencer.get('followers_count', 0):,}")
        st.markdown(f"**💬 카카오 채널 ID:** {influencer.get('kakao_channel_id', 'N/A')}")
        
        # 프로필 텍스트 (멀티라인으로 표시)
        profile_text = influencer.get('profile_text')
        if profile_text and profile_text.strip():
            st.markdown("**📝 프로필 텍스트:**")
            # 텍스트 영역으로 표시하여 멀티라인 지원
            st.text_area(
                "프로필 텍스트 내용",
                value=profile_text,
                height=100,
                disabled=True,
                key=f"profile_text_{influencer['sns_id']}",
                label_visibility="collapsed"
            )


def render_campaign_participation_tab():
    """캠페인 참여 인플루언서 관리 탭"""
    st.subheader("👥 참여 인플루언서 관리")
    st.markdown("캠페인별로 참여 인플루언서를 관리합니다.")
    
    # 캠페인 목록 새로고침 버튼
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 캠페인 목록 새로고침", key="refresh_campaigns_participation", help="캠페인 목록을 새로 불러옵니다"):
            st.rerun()
    
    with col2:
        st.caption("캠페인 목록을 새로고침하려면 새로고침 버튼을 클릭하세요.")
    
    # 캠페인 선택 (모든 캠페인 조회)
    campaigns = db_manager.get_campaigns()
    
    if not campaigns:
        st.info("먼저 캠페인을 생성해주세요.")
        return
    
    campaign_options = {f"{c['campaign_name']} ({c['campaign_type']})": c['id'] for c in campaigns}
    selected_campaign_id = st.selectbox(
        "캠페인 선택",
        options=list(campaign_options.keys()),
        key="participation_campaign_select",
        help="참여 인플루언서를 관리할 캠페인을 선택하세요"
    )
    
    if not selected_campaign_id:
        st.warning("캠페인을 선택해주세요.")
        return
    
    campaign_id = campaign_options[selected_campaign_id]
    selected_campaign = next(c for c in campaigns if c['id'] == campaign_id)
    
    st.subheader(f"📊 {selected_campaign['campaign_name']} 참여 인플루언서")
    
    # 인플루언서 추가 섹션 (새로운 워크플로우)
    render_add_influencer_workflow(campaign_id)
    
    # 참여 인플루언서 목록
    st.subheader("📋 참여 인플루언서 목록")
    
    # 참여 인플루언서 목록 컴팩트 스타일
    st.markdown("""
    <style>
    /* 참여 인플루언서 목록 컴팩트 스타일 */
    div[data-testid="column"] .stButton > button {
        height: 1.5rem !important;
        min-height: 1.5rem !important;
        width: 100% !important;
        font-size: 0.75rem !important;
        padding: 0.1rem 0.3rem !important;
        margin: 0.1rem 0 !important;
    }
    
    /* 리스트 아이템 간격 줄이기 */
    .stContainer {
        margin: 0.1rem 0 !important;
        padding: 0.2rem 0 !important;
    }
    
    /* 텍스트 크기 줄이기 */
    .stMarkdown {
        margin: 0.05rem 0 !important;
        line-height: 1.2 !important;
    }
    
    /* 캡션 텍스트 크기 줄이기 */
    .stCaption {
        font-size: 0.7rem !important;
        margin: 0.02rem 0 !important;
        line-height: 1.1 !important;
    }
    
    /* 제목 텍스트 크기 조정 */
    .stMarkdown h3 {
        margin: 0.1rem 0 !important;
        font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    participations = db_manager.get_campaign_participations(campaign_id)
    
    if participations:
        # 페이지네이션을 위한 설정
        items_per_page = 20
        total_pages = (len(participations) - 1) // items_per_page + 1
        
        # 페이지 선택
        if total_pages > 1:
            page = st.selectbox("페이지 선택", range(1, total_pages + 1), key="participation_page") - 1
            start_idx = page * items_per_page
            end_idx = min(start_idx + items_per_page, len(participations))
            page_participations = participations[start_idx:end_idx]
            st.caption(f"페이지 {page + 1}/{total_pages} (총 {len(participations)}명)")
        else:
            page_participations = participations
        
        for i, participation in enumerate(page_participations):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    # 모든 필드 정보 표시 (컴팩트하게)
                    st.markdown(f"**{participation.get('influencer_name') or participation['sns_id']}**")
                    st.caption(f"📱 SNS ID: {participation['sns_id']} | 👥 팔로워: {participation.get('followers_count', 0):,}명")
                    st.caption(f"🌐 플랫폼: {participation['platform']} | 📦 샘플상태: {participation['sample_status']}")
                    st.caption(f"💰 비용: {participation['cost_krw']:,}원 | 📤 업로드: {'✅' if participation['content_uploaded'] else '❌'}")
                    
                    # 컨텐츠 링크 표시 (첫 번째 링크만)
                    content_links = participation.get('content_links', [])
                    if content_links and len(content_links) > 0:
                        first_link = content_links[0]
                        link_count = len(content_links)
                        if link_count > 1:
                            st.caption(f"🔗 컨텐츠 링크: {first_link} (+{link_count-1}개 더)")
                        else:
                            st.caption(f"🔗 컨텐츠 링크: {first_link}")
                    
                    if participation['manager_comment']:
                        st.caption(f"💬 담당자 의견: {participation['manager_comment']}")
                    if participation['influencer_requests']:
                        st.caption(f"📋 요청사항: {participation['influencer_requests']}")
                    if participation['memo']:
                        st.caption(f"📝 메모: {participation['memo']}")
                    if participation['influencer_feedback']:
                        st.caption(f"💭 피드백: {participation['influencer_feedback']}")
                
                with col2:
                    if st.button("상세보기", key=f"detail_participation_{participation['id']}_{i}"):
                        st.session_state.viewing_participation = participation
                        st.rerun()
                
                with col3:
                    if st.button("수정", key=f"edit_participation_{participation['id']}_{i}"):
                        st.session_state.editing_participation = participation
                        st.rerun()
                
                with col4:
                    if st.button("제거", key=f"remove_participation_{participation['id']}_{i}"):
                        result = db_manager.remove_influencer_from_campaign(participation['id'])
                        if result["success"]:
                            st.success("인플루언서가 제거되었습니다!")
                            st.rerun()
                        else:
                            st.error(f"제거 실패: {result['message']}")
                
                # 구분선을 더 얇게
                st.markdown("---")
    else:
        st.info("이 캠페인에 참여한 인플루언서가 없습니다.")
    
    # 참여 상세보기 모달
    if 'viewing_participation' in st.session_state:
        render_participation_detail_modal()
    
    # 참여 수정 모달
    if 'editing_participation' in st.session_state:
        render_participation_edit_modal()

def render_participation_detail_modal():
    """참여 상세보기 모달"""
    participation = st.session_state.viewing_participation
    
    with st.expander("📋 참여 상세 정보", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**인플루언서:** {participation.get('influencer_name') or participation['sns_id']}")
            st.markdown(f"**플랫폼:** {participation['platform']}")
            st.markdown(f"**SNS ID:** {participation['sns_id']}")
            st.markdown(f"**팔로워 수:** {participation.get('followers_count', 0):,}")
            st.markdown(f"**게시물 수:** {participation.get('post_count', 0):,}")
        
        with col2:
            st.markdown(f"**샘플 상태:** {participation['sample_status']}")
            st.markdown(f"**비용:** {participation['cost_krw']:,}원")
            st.markdown(f"**업로드 완료:** {'✅' if participation['content_uploaded'] else '❌'}")
            st.markdown(f"**참여일:** {participation['created_at'][:10] if participation['created_at'] else 'N/A'}")
        
        if participation['manager_comment']:
            st.markdown("**담당자 의견:**")
            st.info(participation['manager_comment'])
        
        if participation['influencer_requests']:
            st.markdown("**인플루언서 요청사항:**")
            st.info(participation['influencer_requests'])
        
        if participation['influencer_feedback']:
            st.markdown("**인플루언서 피드백:**")
            st.info(participation['influencer_feedback'])
        
        if participation['memo']:
            st.markdown("**메모:**")
            st.info(participation['memo'])
        
        content_links = participation.get('content_links', [])
        if content_links and len(content_links) > 0:
            st.markdown("**컨텐츠 링크:**")
            first_link = content_links[0]
            link_count = len(content_links)
            if link_count > 1:
                st.markdown(f"- {first_link}")
                st.caption(f"총 {link_count}개의 링크가 있습니다. (첫 번째 링크만 표시)")
            else:
                st.markdown(f"- {first_link}")
        
        if st.button("닫기", key="close_participation_detail"):
            del st.session_state.viewing_participation
            st.rerun()

def render_participation_edit_modal():
    """참여 수정 모달"""
    participation = st.session_state.editing_participation
    
    with st.expander("✏️ 참여 정보 수정", expanded=True):
        with st.form("edit_participation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                sample_status = st.selectbox(
                    "샘플 상태",
                    ["요청", "발송준비", "발송완료", "수령"],
                    index=["요청", "발송준비", "발송완료", "수령"].index(participation['sample_status']),
                    key="edit_sample_status"
                )
                cost_krw = st.number_input(
                    "비용 (원)",
                    min_value=0,
                    value=int(participation['cost_krw']),
                    key="edit_cost_krw"
                )
                content_uploaded = st.checkbox(
                    "컨텐츠 업로드 완료",
                    value=participation['content_uploaded'],
                    key="edit_content_uploaded"
                )
            
            with col2:
                manager_comment = st.text_area(
                    "담당자 의견",
                    value=participation['manager_comment'] or "",
                    key="edit_manager_comment"
                )
                influencer_requests = st.text_area(
                    "인플루언서 요청사항",
                    value=participation['influencer_requests'] or "",
                    key="edit_influencer_requests"
                )
                memo = st.text_area(
                    "메모",
                    value=participation['memo'] or "",
                    key="edit_memo"
                )
            
            influencer_feedback = st.text_area(
                "인플루언서 피드백",
                value=participation['influencer_feedback'] or "",
                key="edit_influencer_feedback"
            )
            
            # 컨텐츠 링크 관리
            st.markdown("**컨텐츠 링크:**")
            
            # 버튼 정렬을 위한 CSS
            st.markdown("""
            <style>
            .stButton > button {
                height: 2.5rem !important;
                min-height: 2.5rem !important;
                align-self: flex-end !important;
            }
            .stColumns > div {
                display: flex !important;
                align-items: flex-end !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # 세션 상태에서 링크 관리
            if f"content_links_{participation['id']}" not in st.session_state:
                st.session_state[f"content_links_{participation['id']}"] = participation['content_links'] or []
            
            content_links = st.session_state[f"content_links_{participation['id']}"]
            
            # 기존 링크 표시
            for i, link in enumerate(content_links):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text_input(f"링크 {i+1}", value=link, key=f"existing_link_{i}", disabled=True)
                with col2:
                    # 마이너스 버튼으로 삭제
                    if st.form_submit_button("➖", key=f"delete_link_{i}", help="링크 삭제"):
                        # 삭제할 링크를 None으로 표시
                        content_links[i] = None
                        # None 값 제거 (삭제된 링크들)
                        content_links = [link for link in content_links if link is not None]
                        st.session_state[f"content_links_{participation['id']}"] = content_links
                        st.rerun()
            
            # None 값 제거 (삭제된 링크들)
            content_links = [link for link in content_links if link is not None]
            st.session_state[f"content_links_{participation['id']}"] = content_links
            
            # 새 링크 추가
            col1, col2 = st.columns([4, 1])
            with col1:
                new_link = st.text_input("새 링크 추가", key="new_content_link", placeholder="https://...")
            with col2:
                if st.form_submit_button("➕", key="add_content_link", help="링크 추가"):
                    if new_link and new_link.strip():
                        content_links.append(new_link.strip())
                        st.session_state[f"content_links_{participation['id']}"] = content_links
                        st.rerun()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("수정 완료", type="primary"):
                    updates = {
                        "sample_status": sample_status,
                        "cost_krw": cost_krw,
                        "content_uploaded": content_uploaded,
                        "manager_comment": manager_comment,
                        "influencer_requests": influencer_requests,
                        "memo": memo,
                        "influencer_feedback": influencer_feedback,
                        "content_links": content_links
                    }
                    
                    result = db_manager.update_campaign_participation(participation['id'], updates)
                    if result["success"]:
                        st.success("참여 정보가 수정되었습니다!")
                        # 세션 상태 정리
                        del st.session_state.editing_participation
                        if f"content_links_{participation['id']}" in st.session_state:
                            del st.session_state[f"content_links_{participation['id']}"]
                        st.rerun()
                    else:
                        st.error(f"수정 실패: {result['message']}")
            
            with col2:
                if st.form_submit_button("취소"):
                    # 세션 상태 정리
                    del st.session_state.editing_participation
                    if f"content_links_{participation['id']}" in st.session_state:
                        del st.session_state[f"content_links_{participation['id']}"]
                    st.rerun()

def render_influencer_tab():
    """인플루언서 탭"""
    st.subheader("👥 인플루언서 관리")
    
    # 새 인플루언서 등록
    with st.expander("➕ 새 인플루언서 등록", expanded=True):
        with st.form("create_influencer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                platform = st.selectbox(
                    "플랫폼",
                    ["instagram", "youtube", "tiktok", "twitter"],
                    key="create_influencer_platform",
                    format_func=lambda x: {
                        "instagram": "📸 Instagram",
                        "youtube": "📺 YouTube",
                        "tiktok": "🎵 TikTok",
                        "twitter": "🐦 Twitter"
                    }[x]
                )
                sns_id = st.text_input("SNS ID", placeholder="@username 또는 username")
            
            with col2:
                display_name = st.text_input("표시 이름", placeholder="인플루언서의 표시 이름")
                profile_url = st.text_input("프로필 URL", placeholder="https://...")
            
            col3, col4 = st.columns(2)
            with col3:
                follower_count = st.number_input("팔로워 수", min_value=0, value=0)
            with col4:
                engagement_rate = st.number_input("참여율 (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            
            if st.form_submit_button("인플루언서 등록", type="primary"):
                if not sns_id:
                    st.error("SNS ID를 입력해주세요.")
                else:
                    influencer = Influencer(
                        platform=platform,
                        sns_id=sns_id,
                        display_name=display_name,
                        profile_url=profile_url,
                        follower_count=follower_count,
                        engagement_rate=engagement_rate
                    )
                    
                    result = db_manager.create_influencer(influencer)
                    if result["success"]:
                        st.success("인플루언서가 등록되었습니다!")
                        st.rerun()
                    else:
                        st.error(f"인플루언서 등록 실패: {result['message']}")
    
    # 기존 인플루언서 목록 (캐싱 적용)
    st.subheader("👥 인플루언서 목록")
    
    # 캐시 키 생성
    cache_key = "influencers_data"
    
    # 세션 상태에서 캐시된 데이터 확인
    if cache_key not in st.session_state:
        with st.spinner("인플루언서 데이터를 불러오는 중..."):
            st.session_state[cache_key] = db_manager.get_influencers()
    
    # 캐시된 데이터 사용
    influencers = st.session_state[cache_key]
    
    # 데이터 새로고침 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📊 총 {len(influencers)}명의 인플루언서 데이터가 캐시되어 있습니다.")
    with col2:
        if st.button("🔄 새로고침", help="데이터베이스에서 최신 데이터를 다시 불러옵니다", key="refresh_influencers"):
            with st.spinner("데이터를 새로고침하는 중..."):
                st.session_state[cache_key] = db_manager.get_influencers()
            st.success("데이터가 새로고침되었습니다!")
            st.rerun()
    
    if influencers:
        # 플랫폼별 필터
        platform_filter = st.selectbox(
            "플랫폼 필터",
            ["전체", "instagram", "youtube", "tiktok", "twitter"],
            key="influencer_list_platform_filter",
            format_func=lambda x: {
                "전체": "🌐 전체",
                "instagram": "📸 Instagram",
                "youtube": "📺 YouTube",
                "tiktok": "🎵 TikTok",
                "twitter": "🐦 Twitter"
            }[x]
        )
        
        filtered_influencers = influencers if platform_filter == "전체" else [inf for inf in influencers if inf['platform'] == platform_filter]
        
        for i, influencer in enumerate(filtered_influencers):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{influencer.get('influencer_name') or influencer['sns_id']}**")
                    st.caption(f"플랫폼: {influencer['platform']} | 팔로워: {influencer.get('followers_count', 0):,} | 게시물: {influencer.get('post_count', 0):,}")
                
                with col2:
                    if st.button("편집", key=f"edit_{influencer['id']}_{i}"):
                        st.session_state.editing_influencer = influencer
                        st.rerun()
                
                with col3:
                    if st.button("삭제", key=f"delete_inf_{influencer['id']}_{i}"):
                        result = db_manager.delete_influencer(influencer['id'])
                        if result["success"]:
                            st.success("인플루언서가 삭제되었습니다!")
                            st.rerun()
                        else:
                            st.error(f"삭제 실패: {result['message']}")
                
                st.divider()
    else:
        st.info("등록된 인플루언서가 없습니다.")

def render_performance_crawl():
    """성과관리 크롤링 컴포넌트"""
    st.subheader("📈 성과관리 크롤링")
    st.markdown("캠페인별 성과를 확인하고 인플루언서의 성과를 관리합니다.")
    
    # 캠페인 선택
    campaigns = db_manager.get_campaigns()
    
    if not campaigns:
        st.info("먼저 캠페인을 생성해주세요.")
        return
    
    campaign_options = {f"{c['campaign_name']} ({c['campaign_type']})": c['id'] for c in campaigns}
    selected_campaign_id = st.selectbox(
        "캠페인 선택",
        options=list(campaign_options.keys()),
        key="performance_crawl_campaign_select",
        help="성과를 확인할 캠페인을 선택하세요"
    )
    
    if not selected_campaign_id:
        st.warning("캠페인을 선택해주세요.")
        return
    
    campaign_id = campaign_options[selected_campaign_id]
    selected_campaign = next(c for c in campaigns if c['id'] == campaign_id)
    
    st.subheader(f"📊 {selected_campaign['campaign_name']} 성과 현황")
    
    # 캠페인 기본 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("캠페인 유형", selected_campaign['campaign_type'])
    with col2:
        st.metric("상태", selected_campaign['status'])
    with col3:
        st.metric("시작일", selected_campaign['start_date'])
    with col4:
        st.metric("종료일", selected_campaign['end_date'] or "미정")
    
    # 캠페인에 할당된 인플루언서 목록
    campaign_influencers = db_manager.get_campaign_influencers(campaign_id)
    
    if not campaign_influencers:
        st.info("이 캠페인에 할당된 인플루언서가 없습니다.")
        return
    
    st.subheader("👥 할당된 인플루언서 성과")
    
    for i, ci in enumerate(campaign_influencers):
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{ci.get('influencer_name') or ci['sns_id']}**")
                st.caption(f"플랫폼: {ci['platform']} | 상태: {ci['status']}")
            
            with col2:
                if st.button("성과 크롤링", key=f"crawl_{ci['id']}_{i}"):
                    st.session_state.crawling_influencer = ci
                    st.rerun()
            
            with col3:
                if st.button("성과 입력", key=f"input_{ci['id']}_{i}"):
                    st.session_state.inputting_performance = ci
                    st.rerun()
            
            with col4:
                if st.button("상세보기", key=f"detail_{ci['id']}_{i}"):
                    st.session_state.viewing_performance = ci
                    st.rerun()
            
            # 성과 지표 표시
            metrics = db_manager.get_performance_metrics(campaign_id, ci['influencer_id'])
            if metrics:
                metric_cols = st.columns(len(metrics))
                for i, metric in enumerate(metrics):
                    with metric_cols[i]:
                        st.metric(
                            metric['metric_type'].title(),
                            f"{metric['metric_value']:,}",
                            help=f"측정일: {metric['measurement_date'][:10] if metric['measurement_date'] else 'N/A'}"
                        )
            
            st.divider()
    
    # 성과 크롤링 모달
    if 'crawling_influencer' in st.session_state:
        render_performance_crawling_modal()
    
    # 성과 입력 모달
    if 'inputting_performance' in st.session_state:
        render_performance_input_modal()
    
    # 성과 상세보기 모달
    if 'viewing_performance' in st.session_state:
        render_performance_detail_modal()

def render_performance_management():
    """성과 관리 컴포넌트"""
    st.subheader("📈 성과 관리")
    st.markdown("캠페인별 성과를 확인하고 인플루언서의 성과를 관리합니다.")
    
    # 캠페인 목록 새로고침 버튼
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 캠페인 목록 새로고침", key="refresh_campaigns_performance", help="캠페인 목록을 새로 불러옵니다"):
            st.rerun()
    
    with col2:
        st.caption("캠페인 목록을 새로고침하려면 새로고침 버튼을 클릭하세요.")
    
    # 캠페인 선택 (모든 캠페인 조회)
    campaigns = db_manager.get_campaigns()
    
    if not campaigns:
        st.info("먼저 캠페인을 생성해주세요.")
        return
    
    campaign_options = {f"{c['campaign_name']} ({c['campaign_type']})": c['id'] for c in campaigns}
    selected_campaign_id = st.selectbox(
        "캠페인 선택",
        options=list(campaign_options.keys()),
        key="performance_management_campaign_select",
        help="성과를 확인할 캠페인을 선택하세요"
    )
    
    if not selected_campaign_id:
        st.warning("캠페인을 선택해주세요.")
        return
    
    campaign_id = campaign_options[selected_campaign_id]
    selected_campaign = next(c for c in campaigns if c['id'] == campaign_id)
    
    st.subheader(f"📊 {selected_campaign['campaign_name']} 성과 현황")
    
    # 캠페인 기본 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("캠페인 유형", selected_campaign['campaign_type'])
    with col2:
        st.metric("상태", selected_campaign['status'])
    with col3:
        st.metric("시작일", selected_campaign['start_date'])
    with col4:
        st.metric("종료일", selected_campaign['end_date'] or "미정")
    
    # 캠페인에 참여한 인플루언서 목록
    campaign_participations = db_manager.get_campaign_participations(campaign_id)
    
    if not campaign_participations:
        st.info("이 캠페인에 참여한 인플루언서가 없습니다.")
        return
    
    st.subheader("👥 참여 인플루언서 성과")
    
    for i, participation in enumerate(campaign_participations):
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{participation.get('influencer_name') or participation['sns_id']}**")
                st.caption(f"플랫폼: {participation['platform']} | 샘플상태: {participation['sample_status']}")
                st.caption(f"비용: {participation['cost_krw']:,}원 | 업로드: {'✅' if participation['content_uploaded'] else '❌'}")
            
            with col2:
                if st.button("성과 크롤링", key=f"perf_crawl_{participation['id']}_{i}"):
                    st.session_state.crawling_influencer = participation
                    st.rerun()
            
            with col3:
                if st.button("성과 입력", key=f"perf_input_{participation['id']}_{i}"):
                    st.session_state.inputting_performance = participation
                    st.rerun()
            
            with col4:
                if st.button("상세보기", key=f"perf_detail_{participation['id']}_{i}"):
                    st.session_state.viewing_performance = participation
                    st.rerun()
            
            # 성과 지표 표시
            metrics = db_manager.get_performance_metrics(campaign_id, participation['influencer_id'])
            if metrics:
                metric_cols = st.columns(len(metrics))
                for j, metric in enumerate(metrics):
                    with metric_cols[j]:
                        st.metric(
                            metric['metric_type'].title(),
                            f"{metric['metric_value']:,}",
                            help=f"측정일: {metric['measurement_date'][:10] if metric['measurement_date'] else 'N/A'}"
                        )
            
            st.divider()
    
    # 성과 크롤링 모달
    if 'crawling_influencer' in st.session_state:
        render_performance_crawling_modal()
    
    # 성과 입력 모달
    if 'inputting_performance' in st.session_state:
        render_performance_input_modal()
    
    # 성과 상세보기 모달
    if 'viewing_performance' in st.session_state:
        render_performance_detail_modal()

def render_performance_crawling_modal():
    """성과 크롤링 모달"""
    influencer = st.session_state.crawling_influencer
    
    st.subheader(f"🔍 {influencer.get('influencer_name') or influencer['sns_id']} 성과 크롤링")
    
    if st.button("❌ 닫기", key="close_crawling_modal"):
        del st.session_state.crawling_influencer
        st.rerun()
    
    # 크롤링 옵션
    debug_mode = st.checkbox("🔍 디버그 모드", help="페이지의 HTML 요소들을 확인할 수 있습니다", key="performance_crawl_debug_mode")
    
    if st.button("🚀 성과 크롤링 시작", type="primary", key="performance_crawl_start"):
        with st.spinner(""):
            try:
                crawler = InstagramCrawler()
                
                # URL 생성
                if influencer['platform'] == 'instagram':
                    url = f"https://www.instagram.com/{influencer['sns_id'].replace('@', '')}/"
                    result = crawler.crawl_instagram_post(url, debug_mode)
                else:
                    st.warning(f"{influencer['platform']} 크롤링은 아직 지원되지 않습니다.")
                    return
                
                crawler.close_driver()
                
                if result['status'] == 'success':
                    st.success("성과 크롤링이 완료되었습니다!")
                    
                    # 성과 지표 저장
                    performance_metric = PerformanceMetric(
                        project_id=st.session_state.get('selected_project_id'),
                        influencer_id=influencer['influencer_id'],
                        metric_type='likes',
                        metric_value=result['likes']
                    )
                    
                    db_manager.create_performance_metric(performance_metric)
                    
                    # 댓글 수도 저장
                    performance_metric_comments = PerformanceMetric(
                        project_id=st.session_state.get('selected_project_id'),
                        influencer_id=influencer['influencer_id'],
                        metric_type='comments',
                        metric_value=result['comments']
                    )
                    
                    db_manager.create_performance_metric(performance_metric_comments)
                    
                    st.info("성과 지표가 저장되었습니다.")
                else:
                    st.error(f"크롤링 실패: {result.get('error', '알 수 없는 오류')}")
                    
            except Exception as e:
                st.error(f"크롤링 중 오류가 발생했습니다: {str(e)}")

def render_performance_input_modal():
    """성과 입력 모달"""
    influencer = st.session_state.inputting_performance
    
    st.subheader(f"📝 {influencer.get('influencer_name') or influencer['sns_id']} 성과 입력")
    
    if st.button("❌ 닫기", key="close_input_modal"):
        del st.session_state.inputting_performance
        st.rerun()
    
    with st.form("performance_input_form"):
        metric_type = st.selectbox(
            "지표 유형",
            ["likes", "comments", "shares", "views", "clicks", "conversions"],
            key="performance_metric_type",
            format_func=lambda x: {
                "likes": "❤️ 좋아요",
                "comments": "💬 댓글",
                "shares": "🔄 공유",
                "views": "👁️ 조회수",
                "clicks": "🖱️ 클릭수",
                "conversions": "💰 전환수"
            }[x]
        )
        
        metric_value = st.number_input("지표 값", min_value=0, value=0)
        measurement_date = st.date_input("측정일")
        
        if st.form_submit_button("성과 저장", type="primary"):
            performance_metric = PerformanceMetric(
                project_id=st.session_state.get('selected_project_id'),
                influencer_id=influencer['influencer_id'],
                metric_type=metric_type,
                metric_value=metric_value,
                measurement_date=measurement_date
            )
            
            result = db_manager.create_performance_metric(performance_metric)
            if result["success"]:
                st.success("성과가 저장되었습니다!")
                st.rerun()
            else:
                st.error(f"저장 실패: {result['message']}")

def render_performance_detail_modal():
    """성과 상세보기 모달"""
    influencer = st.session_state.viewing_performance
    
    st.subheader(f"📊 {influencer.get('influencer_name') or influencer['sns_id']} 성과 상세")
    
    if st.button("❌ 닫기", key="close_detail_modal"):
        del st.session_state.viewing_performance
        st.rerun()
    
    # 성과 지표 히스토리
    metrics = db_manager.get_performance_metrics(
        st.session_state.get('selected_project_id'),
        influencer['influencer_id']
    )
    
    if metrics:
        # 데이터프레임으로 표시
        df = pd.DataFrame(metrics)
        df['measurement_date'] = pd.to_datetime(df['measurement_date']).dt.strftime('%Y-%m-%d')
        
        st.dataframe(df, use_container_width=True)
        
        # 차트 표시
        if len(df) > 1:
            st.subheader("📈 성과 추이")
            
            # 지표별로 차트 생성
            metric_types = df['metric_type'].unique()
            for metric_type in metric_types:
                metric_data = df[df['metric_type'] == metric_type].sort_values('measurement_date')
                
                if len(metric_data) > 1:
                    st.line_chart(
                        metric_data.set_index('measurement_date')['metric_value'],
                        use_container_width=True
                    )
    else:
        st.info("성과 데이터가 없습니다.")
