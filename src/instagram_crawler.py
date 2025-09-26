import streamlit as st
import time
import re
import random
import openpyxl
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import asyncio
import logging

# WebSocket 에러 방어를 위한 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_streamlit_update(progress_bar, progress_text, status_text, progress, current, total, message):
    """WebSocket 에러를 방어하는 안전한 Streamlit 업데이트 함수"""
    try:
        # 연결 상태 확인
        if hasattr(st, '_session_state') and st._session_state:
            progress_bar.progress(progress)
            progress_text.text(f"진행률: {current}/{total} ({progress*100:.1f}%)")
            status_text.text(f"상태: {message}")
    except Exception as e:
        # WebSocket 에러나 기타 예외 발생 시 로그만 남기고 조용히 무시
        logger.warning(f"Streamlit 업데이트 실패 (정상적인 상황일 수 있음): {str(e)}")
        pass

class InstagramCrawler:
    def __init__(self):
        self.driver = None
        self._background_tasks = set()  # 백그라운드 태스크 관리
        
    def setup_driver(self):
        """Chrome 드라이버 설정 (Instagram 자동화 감지 우회)"""
        chrome_options = Options()
        
        # 기본 헤드리스 설정
        chrome_options.add_argument("--headless")  # 브라우저 창을 숨김
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # 랜덤 User-Agent (실제 브라우저 시뮬레이션)
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        selected_ua = random.choice(user_agents)
        chrome_options.add_argument(f"--user-agent={selected_ua}")
        
        # 자동화 감지 우회 옵션들 (강화)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # 봇 탐지 회피를 위한 추가 옵션들
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
        
        # 추가 봇 탐지 회피 옵션들
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-component-extensions-with-background-pages")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-domain-reliability")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-hang-monitor")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-prompt-on-repost")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-web-resources")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-field-trial-config")
        chrome_options.add_argument("--disable-back-forward-cache")
        
        # GPU 관련 경고 제거 및 로그 레벨 설정
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-gpu-sandbox")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-gpu-logging")
        chrome_options.add_argument("--disable-gpu-watchdog")
        chrome_options.add_argument("--disable-gpu-process-crash-limit")
        
        # 추가 보안 및 성능 옵션
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # JavaScript로 자동화 속성 숨기기 (강화)
        stealth_scripts = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
            "Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']})",
            "Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})})",
            "Object.defineProperty(navigator, 'platform', {get: () => 'Win32'})",
            "Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4})",
            "Object.defineProperty(navigator, 'deviceMemory', {get: () => 8})",
            "Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0})",
            "Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'})",
            "Object.defineProperty(navigator, 'vendorSub', {get: () => ''})",
            "Object.defineProperty(navigator, 'productSub', {get: () => '20030107'})",
            "Object.defineProperty(navigator, 'appName', {get: () => 'Netscape'})",
            "Object.defineProperty(navigator, 'appVersion', {get: () => '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})",
            "Object.defineProperty(navigator, 'userAgent', {get: () => arguments[0]})",
            "delete navigator.__proto__.webdriver"
        ]
        
        for script in stealth_scripts:
            try:
                if "userAgent" in script:
                    self.driver.execute_script(script, selected_ua)
                else:
                    self.driver.execute_script(script)
            except:
                pass
        
        return self.driver
    
    def simulate_human_behavior(self):
        """자연스러운 사용자 행동 시뮬레이션"""
        try:
            # 랜덤 마우스 움직임
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            
            # 랜덤한 위치로 마우스 이동
            x_offset = random.randint(-100, 100)
            y_offset = random.randint(-100, 100)
            actions.move_by_offset(x_offset, y_offset).perform()
            
            # 랜덤 대기 시간
            time.sleep(random.uniform(0.5, 2.0))
            
            # 랜덤 스크롤
            scroll_amount = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # 다시 위로 스크롤
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            # 에러가 발생해도 크롤링을 계속 진행
            pass
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """랜덤 지연 시간"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def extract_numbers(self, text):
        """텍스트에서 숫자 추출 (K, M, B 단위 및 한글 단위 포함)"""
        if not text:
            return 0
            
        # 공백 제거
        text = text.replace(' ', '').replace(',', '')
        print(f"DEBUG extract_numbers - input: '{text}'")
        
        # K, M, B 단위 처리
        if 'B' in text.upper():
            number = float(re.findall(r'[\d.]+', text)[0])
            result = int(number * 1e9)
            print(f"DEBUG extract_numbers - B unit: {number} * 1e9 = {result}")
            return result
        elif 'M' in text.upper():
            number = float(re.findall(r'[\d.]+', text)[0])
            result = int(number * 1e6)
            print(f"DEBUG extract_numbers - M unit: {number} * 1e6 = {result}")
            return result
        elif 'K' in text.upper():
            number = float(re.findall(r'[\d.]+', text)[0])
            result = int(number * 1e3)
            print(f"DEBUG extract_numbers - K unit: {number} * 1e3 = {result}")
            return result
        # 한글 단위 처리
        elif '만' in text:
            number = float(re.findall(r'[\d.]+', text)[0])
            result = int(number * 10000)
            print(f"DEBUG extract_numbers - 만 unit: {number} * 10000 = {result}")
            return result
        elif '천' in text:
            number = float(re.findall(r'[\d.]+', text)[0])
            result = int(number * 1000)
            print(f"DEBUG extract_numbers - 천 unit: {number} * 1000 = {result}")
            return result
        else:
            numbers = re.findall(r'\d+', text)
            result = int(numbers[0]) if numbers else 0
            print(f"DEBUG extract_numbers - no unit: {result}")
            return result
    
    def crawl_instagram_profile(self, url, debug_mode=False):
        """Instagram 프로필 크롤링"""
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
            
            # 자연스러운 사용자 행동 시뮬레이션
            self.simulate_human_behavior()
            
            # 추가 랜덤 지연
            self.random_delay(1, 3)
            
            # 디버그 모드일 때 페이지 정보 출력
            if debug_mode:
                st.write("🔍 **디버그 정보:**")
                st.write(f"현재 URL: {self.driver.current_url}")
                st.write(f"페이지 제목: {self.driver.title}")
                st.write(f"페이지 소스 길이: {len(self.driver.page_source)}")
            
            # 페이지 로딩 대기 (여러 방법으로 시도)
            try:
                # 1순위: main 태그 대기 (Instagram 최신 버전에서는 없을 수 있음)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
                if debug_mode:
                    st.write("✅ main 태그 발견")
            except TimeoutException:
                if debug_mode:
                    st.info("ℹ️ main 태그 없음 (Instagram 최신 UI 구조)")
                
                try:
                    # 2순위: body 태그 대기
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    if debug_mode:
                        st.write("✅ body 태그 발견")
                except TimeoutException:
                    if debug_mode:
                        st.warning("⚠️ body 태그도 찾을 수 없음")
                    # 3순위: html 태그라도 확인
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.TAG_NAME, "html"))
                        )
                        if debug_mode:
                            st.write("✅ html 태그 발견")
                    except TimeoutException:
                        if debug_mode:
                            st.error("❌ html 태그도 찾을 수 없음 - 페이지 로딩 실패")
                        raise TimeoutException("페이지 로딩 시간 초과")
            
            # 추가 대기 시간 (Instagram의 동적 로딩을 위해)
            time.sleep(random.uniform(2, 4))
            
            # 메타 정보 추출 전 추가 사용자 행동 시뮬레이션
            self.simulate_human_behavior()
            
            # 디버그 모드일 때 페이지 상태 확인
            if debug_mode:
                st.write("🔍 **페이지 상태 확인:**")
                st.write(f"현재 URL: {self.driver.current_url}")
                st.write(f"페이지 제목: {self.driver.title}")
                
                # 메타 태그 존재 여부 확인
                try:
                    og_image = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                    st.write("✅ og:image 메타 태그 존재")
                except:
                    st.warning("⚠️ og:image 메타 태그 없음")
                
                try:
                    og_description = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
                    st.write("✅ og:description 메타 태그 존재")
                except:
                    st.warning("⚠️ og:description 메타 태그 없음")
                
                try:
                    title = self.driver.find_element(By.TAG_NAME, 'title')
                    st.write(f"✅ title 태그: {title.text}")
                except:
                    st.warning("⚠️ title 태그 없음")
            
            # 프로필 정보 추출
            profile_data = {
                'profile_image_url': '',
                'influencer_name': '',
                'post_count': 0,
                'followers_count': 0,
                'profile_text': ''
            }
            
            try:
                # 1. 프로필 이미지 URL 추출 (1순위: og:image)
                try:
                    og_image = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                    profile_data['profile_image_url'] = og_image.get_attribute('content')
                    if debug_mode:
                        st.write(f"**프로필 이미지 URL:** {profile_data['profile_image_url']}")
                except Exception as e:
                    if debug_mode:
                        st.warning(f"og:image 추출 실패: {str(e)}")
                
                # 2. 사용자 이름 추출 (1순위: title, 2순위: og:description)
                try:
                    # 1순위: title에서 "이름 (@username)" 패턴 추출
                    title_element = self.driver.find_element(By.TAG_NAME, 'title')
                    title_text = title_element.text
                    
                    if debug_mode:
                        st.write(f"**Title:** {title_text}")
                    
                    if title_text:
                        import re
                        # "Kim Hana (@she_tasteslikehappiness) • Instagram photos and videos" 패턴
                        name_match = re.search(r'^([^(]+)\s*\(@[^)]+\)', title_text)
                        if name_match:
                            profile_data['influencer_name'] = name_match.group(1).strip()
                            if debug_mode:
                                st.write(f"**Title에서 추출된 이름:** {profile_data['influencer_name']}")
                except Exception as e:
                    if debug_mode:
                        st.warning(f"Title에서 이름 추출 실패: {str(e)}")
                
                # 2순위: og:description에서 이름 추출 (여러 패턴 시도)
                if not profile_data['influencer_name']:
                    try:
                        og_description = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
                        og_content = og_description.get_attribute('content')
                        
                        if debug_mode:
                            st.write(f"**OG Description:** {og_content}")
                        
                        if og_content:
                            import re
                            
                            # 패턴 1: "게시물 885개 - 이름(@username)님의 Instagram" 형식
                            name_match = re.search(r'게시물\s+\d+개\s*-\s*([^(]+)\s*\(@[^)]+\)', og_content)
                            if name_match:
                                profile_data['influencer_name'] = name_match.group(1).strip()
                                if debug_mode:
                                    st.write(f"**OG Description에서 추출된 이름 (패턴1):** {profile_data['influencer_name']}")
                            
                            # 패턴 2: "from 이름 (@username)" 형식 (기존)
                            if not profile_data['influencer_name']:
                                name_match = re.search(r'from\s+([^(]+)\s*\(@[^)]+\)', og_content, re.IGNORECASE)
                                if name_match:
                                    profile_data['influencer_name'] = name_match.group(1).strip()
                                    if debug_mode:
                                        st.write(f"**OG Description에서 추출된 이름 (패턴2):** {profile_data['influencer_name']}")
                            
                            # 패턴 3: "이름(@username)님의 Instagram" 형식
                            if not profile_data['influencer_name']:
                                name_match = re.search(r'([^(]+)\s*\(@[^)]+\)님의\s+Instagram', og_content)
                                if name_match:
                                    profile_data['influencer_name'] = name_match.group(1).strip()
                                    if debug_mode:
                                        st.write(f"**OG Description에서 추출된 이름 (패턴3):** {profile_data['influencer_name']}")
                                        
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"OG Description에서 이름 추출 실패: {str(e)}")
                
                # 3. 게시물 수 추출 (og:description에서)
                try:
                    og_description = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
                    og_content = og_description.get_attribute('content')
                    
                    if og_content:
                        import re
                        # 영문 패턴: "885 Posts"
                        posts_match = re.search(r'([0-9.,KMB]+)\s+Posts?', og_content, re.IGNORECASE)
                        if posts_match:
                            profile_data['post_count'] = self.extract_numbers(posts_match.group(1))
                        else:
                            # 한글 패턴: "게시물 885"
                            posts_match = re.search(r'게시물\s*([0-9.,천만]+)', og_content)
                            if posts_match:
                                profile_data['post_count'] = self.extract_numbers(posts_match.group(1))
                        
                        if debug_mode:
                            st.write(f"**추출된 게시물 수:** {profile_data['post_count']}")
                except Exception as e:
                    if debug_mode:
                        st.warning(f"게시물 수 추출 실패: {str(e)}")
                
                # 4. 팔로워 수 추출 (og:description에서)
                try:
                    og_description = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
                    og_content = og_description.get_attribute('content')
                    
                    if og_content:
                        import re
                        print(f"DEBUG followers - og_content: {og_content}")
                        
                        # 영문 패턴: "48K Followers"
                        followers_match = re.search(r'([0-9.,KMB]+)\s+Followers?', og_content, re.IGNORECASE)
                        if followers_match:
                            raw_followers = followers_match.group(1)
                            print(f"DEBUG followers - 영문 패턴 매칭: '{raw_followers}'")
                            profile_data['followers_count'] = self.extract_numbers(raw_followers)
                        else:
                            # 한글 패턴: "팔로워 48K"
                            followers_match = re.search(r'팔로워\s*([0-9.,천만KMB]+)', og_content)
                            if followers_match:
                                raw_followers = followers_match.group(1)
                                print(f"DEBUG followers - 한글 패턴 매칭: '{raw_followers}'")
                                profile_data['followers_count'] = self.extract_numbers(raw_followers)
                            else:
                                print("DEBUG followers - 패턴 매칭 실패")
                        
                        if debug_mode:
                            st.write(f"**추출된 팔로워 수:** {profile_data['followers_count']}")
                except Exception as e:
                    if debug_mode:
                        st.warning(f"팔로워 수 추출 실패: {str(e)}")
                
                # 5. 프로필 텍스트(bio) 추출 (1순위: JSON-LD, 2순위: meta description)
                try:
                    # 1순위: JSON-LD 스크립트에서 description 추출
                    json_scripts = self.driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
                    for script in json_scripts:
                        try:
                            import json
                            json_data = json.loads(script.get_attribute('innerHTML'))
                            if isinstance(json_data, dict) and 'description' in json_data:
                                profile_data['profile_text'] = json_data['description'].strip()
                                if debug_mode:
                                    st.write(f"**JSON-LD에서 추출된 bio:** {profile_data['profile_text']}")
                                break
                        except:
                            continue
                except Exception as e:
                    if debug_mode:
                        st.warning(f"JSON-LD bio 추출 실패: {str(e)}")
                
                # 2순위: meta description에서 bio 추출 (전체 내용 사용)
                if not profile_data['profile_text']:
                    try:
                        meta_description = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                        content = meta_description.get_attribute('content')
                        
                        if debug_mode:
                            st.write(f"**Meta Description:** {content}")
                        
                        if content:
                            import re
                            # HTML 엔티티로 인코딩된 따옴표 안의 내용 추출 시도
                            bio_match = re.search(r'&quot;([^&]+)&quot;', content)
                            if bio_match:
                                profile_data['profile_text'] = bio_match.group(1).strip()
                                if debug_mode:
                                    st.write(f"**Meta Description에서 추출된 bio (따옴표):** {profile_data['profile_text']}")
                            else:
                                # 일반 따옴표 안의 내용 추출 시도
                                bio_match = re.search(r':\s*"([^"]+)"', content)
                                if bio_match:
                                    profile_data['profile_text'] = bio_match.group(1).strip()
                                    if debug_mode:
                                        st.write(f"**Meta Description에서 추출된 bio (일반 따옴표):** {profile_data['profile_text']}")
                                else:
                                    # 따옴표 패턴이 없으면 전체 Meta Description을 profile_text로 사용
                                    profile_data['profile_text'] = content.strip()
                                    if debug_mode:
                                        st.write(f"**Meta Description 전체를 profile_text로 사용:** {profile_data['profile_text']}")
                            
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"Meta Description bio 추출 실패: {str(e)}")
                
                # 6. Username 추출 (보조 정보)
                username = None
                try:
                    # 1순위: canonical link에서 추출
                    canonical_link = self.driver.find_element(By.CSS_SELECTOR, 'link[rel="canonical"]')
                    canonical_url = canonical_link.get_attribute('href')
                    if canonical_url:
                        username = canonical_url.rstrip('/').split('/')[-1]
                        if debug_mode:
                            st.write(f"**Canonical에서 추출된 username:** {username}")
                except:
                    try:
                        # 2순위: al:ios:url에서 추출
                        ios_url = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="al:ios:url"]')
                        ios_content = ios_url.get_attribute('content')
                        if ios_content:
                            import re
                            username_match = re.search(r'username=([^&]+)', ios_content)
                            if username_match:
                                username = username_match.group(1)
                                if debug_mode:
                                    st.write(f"**iOS URL에서 추출된 username:** {username}")
                    except:
                        try:
                            # 3순위: title의 (@username) 괄호 안에서 추출
                            title_element = self.driver.find_element(By.TAG_NAME, 'title')
                            title_text = title_element.text
                            if title_text:
                                import re
                                username_match = re.search(r'\(@([^)]+)\)', title_text)
                                if username_match:
                                    username = username_match.group(1)
                                    if debug_mode:
                                        st.write(f"**Title에서 추출된 username:** {username}")
                        except:
                            pass
                
                if debug_mode:
                    st.write("**추출된 프로필 데이터:**")
                    for key, value in profile_data.items():
                        st.write(f"- {key}: {value}")
                        
            except Exception as e:
                if debug_mode:
                    st.warning(f"프로필 데이터 추출 중 오류: {str(e)}")
            
            # 페이지 소스와 디버그 정보 수집
            page_source = self.driver.page_source
            debug_info = {
                'current_url': self.driver.current_url,
                'page_title': self.driver.title,
                'page_source_length': len(page_source),
                'crawled_at': datetime.now().isoformat()
            }
            
            return {
                'url': url,
                'profile_image_url': profile_data['profile_image_url'],
                'influencer_name': profile_data['influencer_name'],
                'post_count': profile_data['post_count'],
                'followers_count': profile_data['followers_count'],
                'profile_text': profile_data['profile_text'],
                'status': 'success',
                'page_source': page_source,
                'debug_info': debug_info,
                'raw_profile_data': profile_data
            }
            
        except TimeoutException as e:
            error_msg = f'페이지 로딩 시간 초과: {str(e)}'
            if debug_mode:
                st.error(f"⏰ 타임아웃 에러: {error_msg}")
                st.write("🔍 **타임아웃 디버그 정보:**")
                try:
                    st.write(f"현재 URL: {self.driver.current_url}")
                    st.write(f"페이지 제목: {self.driver.title}")
                    st.write(f"페이지 소스 길이: {len(self.driver.page_source)}")
                    
                    # 페이지 소스 일부 확인
                    page_source = self.driver.page_source
                    if "instagram" in page_source.lower():
                        st.write("✅ Instagram 관련 내용 발견")
                    else:
                        st.write("⚠️ Instagram 관련 내용 없음")
                        
                    if "login" in page_source.lower():
                        st.write("⚠️ 로그인 페이지로 리다이렉트된 것 같음")
                        
                    if "blocked" in page_source.lower() or "restricted" in page_source.lower():
                        st.write("⚠️ 차단되거나 제한된 페이지")
                        
                except Exception as debug_e:
                    st.write(f"디버그 정보 수집 실패: {str(debug_e)}")
                    
            return {
                'url': url,
                'profile_image_url': '',
                'influencer_name': '',
                'post_count': 0,
                'followers_count': 0,
                'profile_text': '',
                'status': 'timeout',
                'error': error_msg
            }
        except Exception as e:
            error_msg = f'크롤링 중 오류 발생: {str(e)}'
            if debug_mode:
                st.error(f"❌ 일반 에러: {error_msg}")
                st.write("🔍 **에러 디버그 정보:**")
                try:
                    st.write(f"현재 URL: {self.driver.current_url}")
                    st.write(f"페이지 제목: {self.driver.title}")
                    st.write(f"에러 타입: {type(e).__name__}")
                    st.write(f"에러 메시지: {str(e)}")
                except Exception as debug_e:
                    st.write(f"디버그 정보 수집 실패: {str(debug_e)}")
                    
            return {
                'url': url,
                'profile_image_url': '',
                'influencer_name': '',
                'post_count': 0,
                'followers_count': 0,
                'profile_text': '',
                'status': 'error',
                'error': error_msg
            }
    
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
            
            # Meta 태그에서 데이터 추출 (가장 안정적인 방법)
            likes = 0
            comments = 0
            
            try:
                # meta description 태그 찾기
                meta_description = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                content = meta_description.get_attribute('content')
                
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
                        
            except Exception as e:
                pass
            
            # Meta 태그에서 추출이 실패한 경우 기존 방식으로 시도
            if likes == 0 or comments == 0:
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
                        pass
                
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
                        pass
            
            return {
                'url': url,
                'likes': likes,
                'comments': comments,
                'status': 'success'
            }
            
        except TimeoutException:
            error_msg = '페이지 로딩 시간 초과'
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
    
    def batch_crawl_instagram_posts(self, excel_data, progress_callback=None, progress_bar=None, progress_text=None, status_text=None):
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
                # 안전한 진행률 업데이트 (크롤링 시작 전)
                if progress_callback and progress_bar and progress_text and status_text:
                    try:
                        progress = min(max((index + 1) / total_posts, 0.0), 1.0)
                        safe_streamlit_update(progress_bar, progress_text, status_text, progress, index + 1, total_posts, f"크롤링 중: {name}")
                    except Exception as e:
                        logger.warning(f"진행률 업데이트 실패: {str(e)}")
                elif progress_callback:
                    # 기존 방식도 지원 (하위 호환성)
                    try:
                        progress_callback(index + 1, total_posts, f"크롤링 중: {name}")
                    except Exception as e:
                        logger.warning(f"기존 진행률 콜백 실패: {str(e)}")
                
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
                    if progress_callback and progress_bar and progress_text and status_text:
                        try:
                            progress = min(max((index + 1) / total_posts, 0.0), 1.0)
                            safe_streamlit_update(progress_bar, progress_text, status_text, progress, index + 1, total_posts, f"쿨다운 중... {cooldown_time}초 대기")
                        except Exception as e:
                            logger.warning(f"쿨다운 진행률 업데이트 실패: {str(e)}")
                    elif progress_callback:
                        try:
                            progress_callback(index + 1, total_posts, f"쿨다운 중... {cooldown_time}초 대기")
                        except Exception as e:
                            logger.warning(f"쿨다운 진행률 콜백 실패: {str(e)}")
                    time.sleep(cooldown_time)
                else:
                    # 마지막 포스트 완료
                    if progress_callback and progress_bar and progress_text and status_text:
                        try:
                            safe_streamlit_update(progress_bar, progress_text, status_text, 1.0, total_posts, total_posts, "크롤링 완료!")
                        except Exception as e:
                            logger.warning(f"완료 진행률 업데이트 실패: {str(e)}")
                    elif progress_callback:
                        try:
                            progress_callback(total_posts, total_posts, "크롤링 완료!")
                        except Exception as e:
                            logger.warning(f"완료 진행률 콜백 실패: {str(e)}")
                    
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
        """드라이버 종료 및 백그라운드 태스크 정리"""
        # 백그라운드 태스크 정리
        for task in list(self._background_tasks):
            try:
                task.cancel()
            except Exception as e:
                logger.warning(f"백그라운드 태스크 취소 실패: {str(e)}")
        self._background_tasks.clear()
        
        # 드라이버 종료
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"드라이버 종료 중 오류: {str(e)}")
            finally:
                self.driver = None
