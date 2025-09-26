import streamlit as st
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import InstagramCrawlResult, InstagramCrawlSession, UserStats
from ..supabase.config import supabase_config

class DatabaseManager:
    def __init__(self):
        self.client = None
        
    def get_client(self):
        """Supabase 클라이언트 반환"""
        if not self.client:
            self.client = supabase_config.get_client()
        return self.client
    
    def get_current_user_id(self) -> Optional[str]:
        """현재 로그인된 사용자 ID 반환 (비로그인시 None)"""
        if 'user' in st.session_state and st.session_state.authenticated:
            return st.session_state.user.id
        return None
    
    def get_or_create_anonymous_user_id(self) -> str:
        """비로그인 사용자를 위한 임시 사용자 ID 생성"""
        if 'anonymous_user_id' not in st.session_state:
            import uuid
            st.session_state.anonymous_user_id = str(uuid.uuid4())
        return st.session_state.anonymous_user_id
    
    # Instagram 크롤링 결과 관련 메서드
    def save_instagram_crawl_result(self, result: InstagramCrawlResult) -> Dict[str, Any]:
        """Instagram 크롤링 결과 저장"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            data = {
                "user_id": user_id,
                "session_id": result.session_id,
                "post_name": result.post_name,
                "post_url": result.post_url,
                "likes": result.likes,
                "comments": result.comments,
                "status": result.status,
                "error_message": result.error_message,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = client.table("instagram_crawl_results").insert(data).execute()
            return {
                "success": True,
                "data": response.data,
                "message": "크롤링 결과가 저장되었습니다."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"크롤링 결과 저장 중 오류가 발생했습니다: {str(e)}"
            }
    
    def get_user_crawl_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """사용자의 Instagram 크롤링 결과 목록 조회"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return []
            
            response = client.table("instagram_crawl_results")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data
        except Exception as e:
            st.error(f"크롤링 결과 조회 중 오류가 발생했습니다: {str(e)}")
            return []
    
    def update_crawl_result_status(self, result_id: str, status: str, error_message: str = None) -> Dict[str, Any]:
        """크롤링 결과 상태 업데이트"""
        try:
            client = self.get_client()
            
            data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if error_message:
                data["error_message"] = error_message
            
            response = client.table("instagram_crawl_results")\
                .update(data)\
                .eq("id", result_id)\
                .execute()
            
            return {
                "success": True,
                "data": response.data,
                "message": "크롤링 결과 상태가 업데이트되었습니다."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"크롤링 결과 상태 업데이트 중 오류가 발생했습니다: {str(e)}"
            }
    
    # Instagram 크롤링 세션 관련 메서드
    def create_instagram_crawl_session(self, session_name: str, total_posts: int) -> Dict[str, Any]:
        """Instagram 크롤링 세션 생성"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            data = {
                "user_id": user_id,
                "session_name": session_name,
                "total_posts": total_posts,
                "status": "running",
                "created_at": datetime.now().isoformat()
            }
            
            response = client.table("instagram_crawl_sessions").insert(data).execute()
            return {
                "success": True,
                "data": response.data,
                "message": "Instagram 크롤링 세션이 생성되었습니다."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Instagram 크롤링 세션 생성 중 오류가 발생했습니다: {str(e)}"
            }
    
    def update_instagram_crawl_session(self, session_id: str, successful_posts: int, failed_posts: int, status: str = "completed") -> Dict[str, Any]:
        """Instagram 크롤링 세션 업데이트"""
        try:
            client = self.get_client()
            
            data = {
                "successful_posts": successful_posts,
                "failed_posts": failed_posts,
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if status == "completed":
                data["completed_at"] = datetime.now().isoformat()
            
            response = client.table("instagram_crawl_sessions")\
                .update(data)\
                .eq("id", session_id)\
                .execute()
            
            return {
                "success": True,
                "data": response.data,
                "message": "Instagram 크롤링 세션이 업데이트되었습니다."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Instagram 크롤링 세션 업데이트 중 오류가 발생했습니다: {str(e)}"
            }
    
    def get_user_instagram_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """사용자의 Instagram 크롤링 세션 목록 조회"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return []
            
            response = client.table("instagram_crawl_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data
        except Exception as e:
            st.error(f"Instagram 크롤링 세션 조회 중 오류가 발생했습니다: {str(e)}")
            return []
    
    # 사용자 통계 관련 메서드
    def get_user_stats(self) -> Optional[Dict[str, Any]]:
        """사용자 통계 조회"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return None
            
            response = client.table("instagram_crawl_stats")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            st.error(f"사용자 통계 조회 중 오류가 발생했습니다: {str(e)}")
            return None
    
    # 프로젝트 관리 관련 메서드
    def create_project(self, project) -> Dict[str, Any]:
        """프로젝트 생성"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return {"success": False, "message": "로그인이 필요합니다."}
            
            project_data = {
                "user_id": user_id,
                "project_name": project.project_name,
                "project_type": project.project_type,
                "description": project.description,
                "status": project.status
            }
            
            response = client.table("projects")\
                .insert(project_data)\
                .execute()
            
            return {"success": True, "data": response.data, "message": "프로젝트가 생성되었습니다."}
        except Exception as e:
            return {"success": False, "message": f"프로젝트 생성 중 오류가 발생했습니다: {str(e)}"}
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """프로젝트 목록 조회"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return []
            
            response = client.table("projects")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return response.data
        except Exception as e:
            st.error(f"프로젝트 조회 중 오류가 발생했습니다: {str(e)}")
            return []
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """프로젝트 삭제"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return {"success": False, "message": "로그인이 필요합니다."}
            
            response = client.table("projects")\
                .delete()\
                .eq("id", project_id)\
                .eq("user_id", user_id)\
                .execute()
            
            return {"success": True, "message": "프로젝트가 삭제되었습니다."}
        except Exception as e:
            return {"success": False, "message": f"프로젝트 삭제 중 오류가 발생했습니다: {str(e)}"}
    
    # 인플루언서 관리 관련 메서드
    def create_influencer(self, influencer) -> Dict[str, Any]:
        """인플루언서 생성 - connecta_influencers 테이블 사용"""
        try:
            client = self.get_client()
            
            influencer_data = {
                "platform": influencer.platform,
                "content_category": "일반",  # 필수 필드
                "sns_id": influencer.sns_id,
                "sns_url": influencer.profile_url or f"https://www.{influencer.platform}.com/{influencer.sns_id}/",
                "influencer_name": influencer.display_name,
                "followers_count": influencer.follower_count,
                "active": True
            }
            
            response = client.table("connecta_influencers")\
                .insert(influencer_data)\
                .execute()
            
            return {"success": True, "data": response.data, "message": "인플루언서가 등록되었습니다."}
        except Exception as e:
            return {"success": False, "message": f"인플루언서 등록 중 오류가 발생했습니다: {str(e)}"}
    
    def get_influencers(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """인플루언서 목록 조회 - connecta_influencers 테이블 사용"""
        try:
            client = self.get_client()
            
            query = client.table("connecta_influencers")\
                .select("id, sns_id, influencer_name, platform, followers_count, post_count, profile_image_url, created_at")\
                .order("created_at", desc=True)
            
            if platform:
                query = query.eq("platform", platform)
            
            response = query.execute()
            return response.data
        except Exception as e:
            st.error(f"인플루언서 조회 중 오류가 발생했습니다: {str(e)}")
            return []
    
    def delete_influencer(self, influencer_id: str) -> Dict[str, Any]:
        """인플루언서 삭제 - connecta_influencers 테이블 사용"""
        try:
            client = self.get_client()
            
            response = client.table("connecta_influencers")\
                .delete()\
                .eq("id", influencer_id)\
                .execute()
            
            return {"success": True, "message": "인플루언서가 삭제되었습니다."}
        except Exception as e:
            return {"success": False, "message": f"인플루언서 삭제 중 오류가 발생했습니다: {str(e)}"}
    
    # 프로젝트-인플루언서 연결 관련 메서드
    def assign_influencer_to_project(self, project_id: str, influencer_id: str) -> Dict[str, Any]:
        """프로젝트에 인플루언서 할당"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return {"success": False, "message": "로그인이 필요합니다."}
            
            assignment_data = {
                "project_id": project_id,
                "influencer_id": influencer_id,
                "status": "assigned"
            }
            
            response = client.table("project_influencers")\
                .insert(assignment_data)\
                .execute()
            
            return {"success": True, "data": response.data, "message": "인플루언서가 할당되었습니다."}
        except Exception as e:
            return {"success": False, "message": f"인플루언서 할당 중 오류가 발생했습니다: {str(e)}"}
    
    def get_project_influencers(self, project_id: str) -> List[Dict[str, Any]]:
        """프로젝트에 할당된 인플루언서 목록 조회"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return []
            
            response = client.table("project_influencers")\
                .select("""
                    *,
                    influencers (
                        id,
                        platform,
                        sns_id,
                        display_name,
                        follower_count,
                        engagement_rate
                    )
                """)\
                .eq("project_id", project_id)\
                .execute()
            
            # 데이터 구조 정리
            result = []
            for item in response.data:
                if item.get('influencers'):
                    influencer_data = item['influencers']
                    result.append({
                        'id': item['id'],
                        'project_id': item['project_id'],
                        'influencer_id': item['influencer_id'],
                        'status': item['status'],
                        'final_output_url': item['final_output_url'],
                        'notes': item['notes'],
                        'assigned_at': item['assigned_at'],
                        'completed_at': item['completed_at'],
                        'platform': influencer_data['platform'],
                        'sns_id': influencer_data['sns_id'],
                        'display_name': influencer_data['display_name'],
                        'follower_count': influencer_data['follower_count'],
                        'engagement_rate': influencer_data['engagement_rate']
                    })
            
            return result
        except Exception as e:
            st.error(f"프로젝트 인플루언서 조회 중 오류가 발생했습니다: {str(e)}")
            return []
    
    # 성과 관리 관련 메서드
    def create_performance_metric(self, metric) -> Dict[str, Any]:
        """성과 지표 생성"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return {"success": False, "message": "로그인이 필요합니다."}
            
            metric_data = {
                "project_id": metric.project_id,
                "influencer_id": metric.influencer_id,
                "metric_type": metric.metric_type,
                "metric_value": metric.metric_value,
                "measurement_date": metric.measurement_date.isoformat() if metric.measurement_date else None
            }
            
            response = client.table("performance_metrics")\
                .insert(metric_data)\
                .execute()
            
            return {"success": True, "data": response.data, "message": "성과 지표가 저장되었습니다."}
        except Exception as e:
            return {"success": False, "message": f"성과 지표 저장 중 오류가 발생했습니다: {str(e)}"}
    
    def get_performance_metrics(self, project_id: str, influencer_id: str) -> List[Dict[str, Any]]:
        """성과 지표 조회"""
        try:
            client = self.get_client()
            user_id = self.get_current_user_id()
            
            if not user_id:
                return []
            
            response = client.table("performance_metrics")\
                .select("*")\
                .eq("project_id", project_id)\
                .eq("influencer_id", influencer_id)\
                .order("measurement_date", desc=True)\
                .execute()
            
            return response.data
        except Exception as e:
            st.error(f"성과 지표 조회 중 오류가 발생했습니다: {str(e)}")
            return []
    
    # 인플루언서 크롤링 관련 메서드
    def check_influencer_exists(self, platform: str, sns_id: str) -> Optional[Dict[str, Any]]:
        """인플루언서가 데이터베이스에 존재하는지 확인 - connecta_influencers 테이블 사용"""
        try:
            client = self.get_client()
            
            # connecta_influencers 테이블에서 sns_id로만 검색
            response = client.table("connecta_influencers")\
                .select("*")\
                .eq("platform", platform)\
                .eq("sns_id", sns_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"인플루언서 존재 확인 중 오류가 발생했습니다: {str(e)}")
            return None
    
    def update_influencer_data(self, influencer_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """인플루언서 데이터 업데이트 - 크롤링 성공한 필드만 업데이트"""
        try:
            client = self.get_client()
            
            # 크롤링으로 업데이트 가능한 필드들만 선별
            update_data = {
                "updated_at": datetime.now().isoformat()
            }
            
            # 크롤링이 성공한 필드들만 업데이트 (빈 값 필터링 강화)
            raw_name = profile_data.get('influencer_name', '')
            if raw_name and raw_name.strip():
                update_data["influencer_name"] = raw_name.strip()
                print(f"DEBUG UPDATE - influencer_name: '{raw_name.strip()}'")
            
            if profile_data.get('followers_count', 0) > 0:
                update_data["followers_count"] = profile_data['followers_count']
            
            if profile_data.get('post_count', 0) > 0:
                update_data["post_count"] = profile_data['post_count']
            
            raw_text = profile_data.get('profile_text', '')
            if raw_text and raw_text.strip():
                update_data["profile_text"] = raw_text.strip()
            
            if profile_data.get('profile_image_url'):
                update_data["profile_image_url"] = profile_data['profile_image_url']
            
            # 업데이트할 데이터가 있는 경우에만 실행
            if len(update_data) > 1:  # updated_at 외에 다른 필드가 있는 경우
                response = client.table("connecta_influencers")\
                    .update(update_data)\
                    .eq("id", influencer_id)\
                    .execute()
                
                return {"success": True, "data": response.data, "message": "인플루언서 데이터가 업데이트되었습니다."}
            else:
                return {"success": True, "data": None, "message": "업데이트할 크롤링 데이터가 없습니다."}
                
        except Exception as e:
            return {"success": False, "message": f"인플루언서 데이터 업데이트 중 오류가 발생했습니다: {str(e)}"}
    
    def create_influencer_from_crawl(self, platform: str, sns_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """크롤링 결과로부터 인플루언서 생성 - connecta_influencers 테이블 사용"""
        try:
            client = self.get_client()
            
            # 인플루언서 데이터 준비 (빈 값 필터링)
            raw_name = profile_data.get('influencer_name', '')
            influencer_name = raw_name.strip() if raw_name and raw_name.strip() else sns_id
            
            raw_text = profile_data.get('profile_text', '')
            profile_text = raw_text.strip() if raw_text and raw_text.strip() else ''
            
            # 디버깅: 최종 influencer_name 확인
            print(f"DEBUG - raw_name: '{raw_name}', influencer_name: '{influencer_name}', sns_id: '{sns_id}'")
            
            influencer_data = {
                "platform": platform,
                "content_category": "일반",  # 필수 필드
                "sns_id": sns_id,
                "sns_url": profile_data.get('profile_image_url', f"https://www.{platform}.com/{sns_id}/"),
                "influencer_name": influencer_name,  # 빈 값이면 sns_id 사용
                "followers_count": profile_data.get('followers_count', 0),
                "post_count": profile_data.get('post_count', 0),
                "profile_text": profile_text,
                "profile_image_url": profile_data.get('profile_image_url', ''),
                "active": True
            }
            
            # connecta_influencers 테이블에 삽입
            response = client.table("connecta_influencers")\
                .insert(influencer_data)\
                .execute()
            
            return {"success": True, "data": response.data, "message": "인플루언서가 생성되었습니다."}
        except Exception as e:
            return {"success": False, "message": f"인플루언서 생성 중 오류가 발생했습니다: {str(e)}"}
    
    def save_crawl_raw_data(self, influencer_id: str, platform: str, sns_id: str, 
                           page_source: str, profile_data: Dict[str, Any], 
                           debug_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """크롤링 원시 데이터를 connecta_influencer_crawl_raw 테이블에 저장 (유효 정보만 추출)"""
        try:
            client = self.get_client()
            
            # 유효한 정보만 추출
            extracted_info = self._extract_meaningful_content(page_source, profile_data)
            
            # 원시 데이터 구성 (HTML/CSS 제거된 유효 정보만)
            raw_data = {
                "page_source_length": len(page_source),
                "extracted_content": extracted_info,
                "profile_data": profile_data,
                "debug_info": debug_info or {},
                "crawled_at": datetime.now().isoformat()
            }
            
            # 콘텐츠 해시 생성 (중복 방지용)
            content_hash = hashlib.md5(
                json.dumps(raw_data, sort_keys=True).encode('utf-8')
            ).hexdigest()
            
            # 저장할 데이터
            crawl_data = {
                "influencer_id": influencer_id,
                "platform": platform,
                "sns_id": sns_id,
                "data_type": "profile",
                "raw_json": raw_data,
                "content_hash": content_hash,
                "source_name": "instagram_crawler",
                "crawled_at": datetime.now().isoformat()
            }
            
            # connecta_influencer_crawl_raw 테이블에 저장
            response = client.table("connecta_influencer_crawl_raw")\
                .insert(crawl_data)\
                .execute()
            
            return {"success": True, "data": response.data, "message": "크롤링 원시 데이터가 저장되었습니다."}
            
        except Exception as e:
            return {"success": False, "message": f"크롤링 원시 데이터 저장 중 오류가 발생했습니다: {str(e)}"}
    
    def _extract_meaningful_content(self, page_source: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """HTML에서 유효한 정보만 추출 (HTML 태그, CSS 제거)"""
        import re
        from bs4 import BeautifulSoup
        
        try:
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 스크립트, 스타일 태그 제거
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # 텍스트 추출
            text_content = soup.get_text()
            
            # 공백 정리
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # 메타 태그에서 유용한 정보 추출
            meta_info = {}
            try:
                # og:description
                og_desc = soup.find('meta', property='og:description')
                if og_desc:
                    meta_info['og_description'] = og_desc.get('content', '')
                
                # og:title
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    meta_info['og_title'] = og_title.get('content', '')
                
                # description
                desc = soup.find('meta', attrs={'name': 'description'})
                if desc:
                    meta_info['description'] = desc.get('content', '')
                
                # title
                title = soup.find('title')
                if title:
                    meta_info['title'] = title.get_text().strip()
                    
            except Exception as e:
                print(f"Meta 정보 추출 실패: {e}")
            
            # 해시태그 추출
            hashtags = re.findall(r'#\w+', clean_text)
            
            # @멘션 추출
            mentions = re.findall(r'@\w+', clean_text)
            
            # URL 추출
            urls = re.findall(r'https?://[^\s<>"]+', clean_text)
            
            # 이모지 추출
            emojis = re.findall(r'[^\w\s#@]', clean_text)
            emojis = [emoji for emoji in emojis if len(emoji.encode('utf-8')) > 2]  # 실제 이모지만
            
            # 숫자 정보 추출 (팔로워, 게시물 수 등)
            numbers = re.findall(r'\d+[KMB]?', clean_text)
            
            return {
                "clean_text": clean_text[:5000],  # 텍스트 길이 제한
                "meta_info": meta_info,
                "hashtags": list(set(hashtags))[:50],  # 중복 제거, 최대 50개
                "mentions": list(set(mentions))[:50],  # 중복 제거, 최대 50개
                "urls": list(set(urls))[:20],  # 중복 제거, 최대 20개
                "emojis": list(set(emojis))[:30],  # 중복 제거, 최대 30개
                "numbers": list(set(numbers))[:20],  # 중복 제거, 최대 20개
                "text_length": len(clean_text),
                "extraction_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"유효 정보 추출 실패: {e}")
            return {
                "error": str(e),
                "fallback_text": page_source[:1000] if page_source else "",  # 실패시 원본 일부만
                "extraction_timestamp": datetime.now().isoformat()
            }
    
    def get_influencer_info(self, platform: str, sns_id: str) -> Dict[str, Any]:
        """인플루언서 정보 조회 (DB 확인용) - connecta_influencers 테이블 사용"""
        try:
            client = self.get_client()
            
            # 디버깅 정보
            debug_info = {
                "platform": platform,
                "sns_id": sns_id,
                "table": "connecta_influencers"
            }
            
            # connecta_influencers 테이블에서 sns_id로만 검색
            # 먼저 정확한 매칭 시도
            response = client.table("connecta_influencers")\
                .select("id, sns_id, influencer_name, content_category, followers_count, post_count, profile_text, profile_image_url, created_at")\
                .eq("platform", platform)\
                .eq("sns_id", sns_id)\
                .execute()
            
            # 정확한 매칭이 실패하면 대소문자 구분 없이 검색
            if not response.data:
                all_influencers = client.table("connecta_influencers")\
                    .select("id, sns_id, influencer_name, content_category, followers_count, post_count, profile_text, profile_image_url, created_at")\
                    .eq("platform", platform)\
                    .execute()
                
                # 대소문자 구분 없이 매칭
                for inf in all_influencers.data:
                    if inf.get("sns_id", "").lower() == sns_id.lower():
                        response.data = [inf]
                        break
            
            debug_info["query_conditions"] = f"platform={platform}, sns_id={sns_id}"
            debug_info["case_insensitive_search"] = True
            debug_info["response_count"] = len(response.data) if response.data else 0
            debug_info["response_data"] = response.data
            
            # 모든 인플루언서 조회 (디버깅용)
            all_influencers = client.table("connecta_influencers")\
                .select("id, sns_id, influencer_name, platform")\
                .eq("platform", platform)\
                .execute()
            
            debug_info["all_influencers"] = all_influencers.data
            
            if response.data:
                influencer = response.data[0]
                return {
                    "success": True,
                    "exists": True,
                    "data": {
                        "id": influencer["id"],
                        "sns_id": influencer["sns_id"],
                        "influencer_name": influencer.get("influencer_name", ""),
                        "content_category": influencer.get("content_category", "일반"),
                        "followers_count": influencer.get("followers_count", 0),
                        "post_count": influencer.get("post_count", 0),
                        "profile_text": influencer.get("profile_text", ""),
                        "profile_url": influencer.get("profile_image_url", ""),
                        "created_at": influencer.get("created_at", "")
                    },
                    "message": "인플루언서 정보를 찾았습니다.",
                    "debug_info": debug_info
                }
            else:
                return {
                    "success": True,
                    "exists": False,
                    "data": None,
                    "message": f"데이터베이스에 해당 인플루언서가 없습니다. (디버그: {debug_info})",
                    "debug_info": debug_info
                }
        except Exception as e:
            return {
                "success": False,
                "exists": False,
                "data": None,
                "message": f"인플루언서 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "debug_info": {"error": str(e), "platform": platform, "sns_id": sns_id}
            }

# 전역 인스턴스
db_manager = DatabaseManager()
