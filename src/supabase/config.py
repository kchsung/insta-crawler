import os
import streamlit as st
from supabase import create_client, Client
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class SupabaseConfig:
    def __init__(self):
        # Streamlit secrets에서 먼저 시도, 없으면 환경변수에서 가져오기
        try:
            secrets = st.secrets["supabase"]
            self.url: str = secrets.get("url", "")
            self.key: str = secrets.get("anon_key", "")
        except:
            # 환경변수에서 가져오기
            self.url: str = os.getenv("SUPABASE_URL", "")
            self.key: str = os.getenv("SUPABASE_ANON_KEY", "")
        
        self.client: Optional[Client] = None
        
    def get_client(self) -> Client:
        """Supabase 클라이언트 인스턴스 반환"""
        if not self.client:
            if not self.url or not self.key:
                raise ValueError("SUPABASE_URL과 SUPABASE_ANON_KEY 환경변수가 설정되어야 합니다.")
            self.client = create_client(self.url, self.key)
        return self.client
    
    def is_configured(self) -> bool:
        """Supabase 설정이 완료되었는지 확인"""
        return bool(self.url and self.key)

# 전역 인스턴스
supabase_config = SupabaseConfig()
