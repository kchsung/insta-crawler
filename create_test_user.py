#!/usr/bin/env python3
"""
테스트용 사용자 생성 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.supabase.config import supabase_config

def create_test_user():
    """테스트용 사용자 생성"""
    try:
        client = supabase_config.get_client()
        
        # 테스트 이메일과 비밀번호
        test_email = "test@example.com"
        test_password = "test123456"
        
        print(f"테스트 사용자 생성 시도: {test_email}")
        
        # 회원가입 시도
        response = client.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        if response.user:
            print("✅ 테스트 사용자 생성 성공!")
            print(f"사용자 ID: {response.user.id}")
            print(f"이메일: {response.user.email}")
            print(f"이메일 확인 상태: {response.user.email_confirmed_at}")
            
            # 바로 로그인 시도
            login_response = client.auth.sign_in_with_password({
                "email": test_email,
                "password": test_password
            })
            
            if login_response.user:
                print("✅ 로그인 성공!")
                print("이제 웹 애플리케이션에서 이 계정으로 로그인할 수 있습니다.")
            else:
                print("❌ 로그인 실패")
        else:
            print("❌ 사용자 생성 실패")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    create_test_user()
