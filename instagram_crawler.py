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

class InstagramCrawler:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Chrome 드라이버 설정 (Instagram 자동화 감지 우회)"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 브라우저 창을 숨김
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # 최신 User-Agent 사용 (2024년 Chrome 120)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 자동화 감지 우회 옵션들
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-field-trial-config")
        chrome_options.add_argument("--disable-back-forward-cache")
        chrome_options.add_argument("--disable-hang-monitor")
        chrome_options.add_argument("--disable-prompt-on-repost")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-translate")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        
        # GPU 관련 경고 제거 및 로그 레벨 설정
        chrome_options.add_argument("--enable-unsafe-swiftshader")  # GPU 경고 해결
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-gpu-sandbox")
        chrome_options.add_argument("--log-level=3")  # FATAL 레벨만 표시
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-gpu-logging")
        chrome_options.add_argument("--disable-gpu-watchdog")
        chrome_options.add_argument("--disable-gpu-process-crash-limit")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # JavaScript로 자동화 속성 숨기기
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']})")
        
        return self.driver
    
    def extract_numbers(self, text):
        """텍스트에서 숫자 추출 (K, M 단위 포함)"""
        if not text:
            return 0
            
        # K, M 단위 처리
        text = text.replace(',', '').replace(' ', '')
        
        if 'K' in text.upper():
            number = float(re.findall(r'[\d.]+', text)[0])
            return int(number * 1000)
        elif 'M' in text.upper():
            number = float(re.findall(r'[\d.]+', text)[0])
            return int(number * 1000000)
        else:
            numbers = re.findall(r'\d+', text)
            return int(numbers[0]) if numbers else 0
    
    def crawl_instagram_post(self, url, debug_mode=False):
        """Instagram 포스트 크롤링 (모바일 버전 최적화)"""
        try:
            if not self.driver:
                self.setup_driver()
            
            # 모바일 User-Agent로 설정
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
            })
            
            self.driver.get(url)
            
            # 랜덤 대기 시간 (3-7초)
            wait_time = random.uniform(3, 7)
            time.sleep(wait_time)
            
            # 자연스러운 브라우저 동작 시뮬레이션
            try:
                # 페이지 스크롤 (자연스러운 사용자 행동)
                self.driver.execute_script("window.scrollTo(0, 100);")
                time.sleep(random.uniform(1, 2))
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
            except:
                pass
            
            # 페이지 로딩 대기 (타임아웃 증가)
            WebDriverWait(self.driver, 25).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # 추가 대기 시간 (Instagram의 동적 로딩을 위해)
            time.sleep(random.uniform(2, 4))
            
            # 디버그 모드일 때 페이지 정보 출력
            if debug_mode:
                st.write("🔍 **디버그 정보:**")
                st.write(f"현재 URL: {self.driver.current_url}")
                st.write(f"페이지 제목: {self.driver.title}")
            
            # Meta 태그에서 데이터 추출 (가장 안정적인 방법)
            likes = 0
            comments = 0
            
            try:
                # meta description 태그 찾기
                meta_description = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                content = meta_description.get_attribute('content')
                
                if debug_mode:
                    st.write(f"**Meta Description:** {content}")
                
                if content:
                    import re
                    # "84 likes, 30 comments" 패턴에서 추출
                    # 좋아요 수 추출
                    like_match = re.search(r'(\d+)\s*likes?', content, re.IGNORECASE)
                    if like_match:
                        likes = int(like_match.group(1))
                    
                    # 댓글 수 추출
                    comment_match = re.search(r'(\d+)\s*comments?', content, re.IGNORECASE)
                    if comment_match:
                        comments = int(comment_match.group(1))
                    
                    if debug_mode:
                        st.write(f"**추출된 데이터:** 좋아요 {likes}, 댓글 {comments}")
                        
            except Exception as e:
                if debug_mode:
                    st.warning(f"Meta 태그 추출 중 오류: {str(e)}")
            
            # Meta 태그에서 추출이 실패한 경우 기존 방식으로 시도
            if likes == 0 or comments == 0:
                if debug_mode:
                    st.write("Meta 태그에서 데이터를 찾을 수 없어 기존 방식으로 시도합니다...")
                
                # 자연스러운 사용자 행동 시뮬레이션
                try:
                    # 마우스 움직임 시뮬레이션
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_by_offset(100, 100).perform()
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # 페이지 새로고침 (자연스러운 행동)
                    self.driver.refresh()
                    time.sleep(random.uniform(3, 5))
                except:
                    pass
                
                # 좋아요 수 추출 - 기존 방식
                if likes == 0:
                    try:
                        like_patterns = [
                            "//span[contains(text(), 'likes')]",
                            "//span[contains(text(), '좋아요')]",
                            "//article//span[contains(text(), 'likes')]",
                            "//main//span[contains(text(), 'likes')]",
                        ]
                        
                        for pattern in like_patterns:
                            try:
                                elements = self.driver.find_elements(By.XPATH, pattern)
                                for element in elements:
                                    text = element.text.strip()
                                    if 'likes' in text.lower() or '좋아요' in text:
                                        import re
                                        like_match = re.search(r'([\d,]+)\s*likes?', text, re.IGNORECASE)
                                        if like_match:
                                            likes = self.extract_numbers(like_match.group(1))
                                            break
                                if likes > 0:
                                    break
                            except:
                                continue
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"좋아요 수 추출 중 오류: {str(e)}")
                
                # 댓글 수 추출 - 기존 방식
                if comments == 0:
                    try:
                        comment_patterns = [
                            "//span[contains(text(), 'View all') and contains(text(), 'comments')]",
                            "//span[contains(text(), 'comments')]",
                            "//article//span[contains(text(), 'comments')]",
                            "//main//span[contains(text(), 'comments')]",
                        ]
                        
                        for pattern in comment_patterns:
                            try:
                                elements = self.driver.find_elements(By.XPATH, pattern)
                                for element in elements:
                                    text = element.text.strip()
                                    if 'comments' in text.lower() or '댓글' in text:
                                        import re
                                        if 'view all' in text.lower():
                                            numbers = re.findall(r'View all (\d+)', text, re.IGNORECASE)
                                            if numbers:
                                                comments = int(numbers[0])
                                                break
                                        else:
                                            numbers = re.findall(r'(\d+)\s*comments?', text, re.IGNORECASE)
                                            if numbers:
                                                comments = int(numbers[0])
                                                break
                                if comments > 0:
                                    break
                            except:
                                continue
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"댓글 수 추출 중 오류: {str(e)}")
            
            return {
                'url': url,
                'likes': likes,
                'comments': comments,
                'status': 'success'
            }
            
        except TimeoutException:
            error_msg = '페이지 로딩 시간 초과'
            if debug_mode:
                st.error(f"⏰ 타임아웃 에러: {error_msg}")
                st.warning("""
                **타임아웃 해결 방법:**
                1. 네트워크 연결 상태를 확인하세요
                2. Instagram 서버가 느릴 수 있으니 잠시 후 재시도하세요
                3. 다른 Instagram 포스트로 테스트해보세요
                4. VPN을 사용 중이라면 비활성화해보세요
                """)
            return {
                'url': url,
                'likes': 0,
                'comments': 0,
                'status': 'timeout',
                'error': error_msg
            }
        except Exception as e:
            return {
                'url': url,
                'likes': 0,
                'comments': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def batch_crawl_instagram_posts(self, excel_data, progress_callback=None):
        """엑셀 데이터로부터 여러 Instagram 포스트 일괄 크롤링"""
        results = []
        total_posts = len(excel_data)
        
        for index, row in excel_data.iterrows():
            # 빈 셀 처리 (NaN 값 처리)
            name = row.get('name', f'Post_{index+1}')
            if pd.isna(name):
                name = f'Post_{index+1}'
            
            url = row.get('instagram_link', '')
            if pd.isna(url):
                url = ''
            
            # URL 유효성 검사
            if not url or not isinstance(url, str) or 'instagram.com' not in url:
                results.append({
                    'name': name,
                    'url': url if isinstance(url, str) else '',
                    'likes': 0,
                    'comments': 0,
                    'status': 'error',
                    'error': 'Invalid URL or Empty Cell'
                })
                continue
            
            try:
                # 진행률 업데이트 (크롤링 시작 전)
                if progress_callback:
                    progress_callback(index + 1, total_posts, f"크롤링 중: {name}")
                
                # 크롤링 실행
                result = self.crawl_instagram_post(url, debug_mode=False)
                
                results.append({
                    'name': name,
                    'url': url,
                    'likes': result['likes'],
                    'comments': result['comments'],
                    'status': result['status'],
                    'error': result.get('error', '')
                })
                
                # 쿨다운 시간 (30-60초 랜덤 - Instagram 감지 우회를 위해 증가)
                if index < total_posts - 1:  # 마지막 포스트가 아닌 경우에만
                    cooldown_time = random.randint(30, 60)
                    if progress_callback:
                        progress_callback(index + 1, total_posts, f"쿨다운 중... {cooldown_time}초 대기")
                    time.sleep(cooldown_time)
                else:
                    # 마지막 포스트 완료
                    if progress_callback:
                        progress_callback(total_posts, total_posts, "크롤링 완료!")
                    
            except Exception as e:
                results.append({
                    'name': name,
                    'url': url,
                    'likes': 0,
                    'comments': 0,
                    'status': 'error',
                    'error': str(e)
                })
                continue
        
        return results
    
    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None

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
            "Instagram 포스트 URL을 입력하세요:",
            placeholder="https://www.instagram.com/p/...",
            help="Instagram 포스트의 전체 URL을 입력해주세요"
        )
        
        if st.button("🔍 크롤링 시작", type="primary"):
            if not url:
                st.error("URL을 입력해주세요!")
            elif "instagram.com" not in url:
                st.error("올바른 Instagram URL을 입력해주세요!")
            else:
                with st.spinner("크롤링 중입니다..."):
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
                    
                else:
                    st.error(f"크롤링 실패: {result.get('error', '알 수 없는 오류')}")
    
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

def batch_crawl_tab():
    """일괄 크롤링 탭"""
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
                return
            
            # 유효한 데이터만 필터링 (instagram_link가 있는 행만)
            valid_df = df.dropna(subset=['instagram_link'])
            valid_df = valid_df[valid_df['instagram_link'].astype(str).str.contains('instagram.com', na=False)]
            
            st.success(f"엑셀 파일이 성공적으로 로드되었습니다. 총 {len(df)}개 행 중 {len(valid_df)}개의 유효한 포스트가 있습니다.")
            
            if len(valid_df) == 0:
                st.warning("유효한 Instagram URL이 없습니다. URL이 올바른지 확인해주세요.")
                return
            
            # 데이터 미리보기
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
                
                # 진행률 콜백 함수
                def update_progress(current, total, message):
                    # 안전한 진행률 계산
                    if total > 0:
                        progress = min(max(current / total, 0.0), 1.0)  # 0.0과 1.0 사이로 제한
                    else:
                        progress = 0.0
                    
                    progress_bar.progress(progress)
                    progress_text.text(f"진행률: {current}/{total} ({progress*100:.1f}%)")
                    status_text.text(f"상태: {message}")
                
                # 크롤링 실행
                with results_container:
                    with st.spinner("일괄 크롤링을 시작합니다..."):
                        crawler = InstagramCrawler()
                        results = crawler.batch_crawl_instagram_posts(valid_df, update_progress)
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
        
        except Exception as e:
            st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {str(e)}")
    
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
    
    ### 주의사항
    - 각 포스트 크롤링 후 20-40초의 랜덤 쿨다운 시간이 있습니다
    - 에러가 발생해도 다음 포스트로 계속 진행됩니다
    - Instagram의 정책을 준수하여 사용하세요
    """)

def main():
    st.set_page_config(
        page_title="Instagram Crawler",
        page_icon="📸",
        layout="wide"
    )
    
    st.title("📸 Instagram 크롤러")
    st.markdown("Instagram 포스트의 좋아요 수와 댓글 수를 추출합니다.")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["📱 단일 크롤링", "📊 일괄 크롤링"])
    
    with tab1:
        single_crawl_tab()
    
    with tab2:
        batch_crawl_tab()
    
    # 사이드바
    with st.sidebar:
        st.header("ℹ️ 정보")
        st.markdown("""
        ### 기능
        - 📱 단일 포스트 크롤링
        - 📊 엑셀 파일 일괄 크롤링
        - 🔍 디버그 모드
        - 📥 결과 다운로드
        
        ### 추출 정보
        - ❤️ 좋아요 수
        - 💬 댓글 수
        
        ### 주의사항
        - Instagram의 정책을 준수하세요
        - 과도한 요청은 피하세요
        - 일부 포스트는 접근이 제한될 수 있습니다
        """)

if __name__ == "__main__":
    main()
