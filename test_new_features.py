#!/usr/bin/env python3
"""
새로운 기능 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.models import Project, Influencer, ProjectInfluencer, PerformanceMetric
from src.db.database import db_manager
from src.supabase.auth import supabase_auth

def test_database_operations():
    """데이터베이스 작업 테스트"""
    print("🧪 새로운 기능 테스트 시작...")
    
    # 1. 프로젝트 생성 테스트
    print("\n1. 프로젝트 생성 테스트")
    project = Project(
        project_name="테스트 프로젝트",
        project_type="seeding",
        description="테스트용 프로젝트입니다.",
        status="active"
    )
    
    result = db_manager.create_project(project)
    if result["success"]:
        print("✅ 프로젝트 생성 성공")
        project_id = result["data"][0]["id"]
    else:
        print(f"❌ 프로젝트 생성 실패: {result['message']}")
        return
    
    # 2. 인플루언서 생성 테스트
    print("\n2. 인플루언서 생성 테스트")
    influencer = Influencer(
        platform="instagram",
        sns_id="@test_influencer",
        display_name="테스트 인플루언서",
        profile_url="https://www.instagram.com/test_influencer/",
        follower_count=10000,
        engagement_rate=5.5
    )
    
    result = db_manager.create_influencer(influencer)
    if result["success"]:
        print("✅ 인플루언서 생성 성공")
        influencer_id = result["data"][0]["id"]
    else:
        print(f"❌ 인플루언서 생성 실패: {result['message']}")
        return
    
    # 3. 프로젝트-인플루언서 연결 테스트
    print("\n3. 프로젝트-인플루언서 연결 테스트")
    result = db_manager.assign_influencer_to_project(project_id, influencer_id)
    if result["success"]:
        print("✅ 프로젝트-인플루언서 연결 성공")
    else:
        print(f"❌ 프로젝트-인플루언서 연결 실패: {result['message']}")
    
    # 4. 성과 지표 생성 테스트
    print("\n4. 성과 지표 생성 테스트")
    metric = PerformanceMetric(
        project_id=project_id,
        influencer_id=influencer_id,
        metric_type="likes",
        metric_value=1500
    )
    
    result = db_manager.create_performance_metric(metric)
    if result["success"]:
        print("✅ 성과 지표 생성 성공")
    else:
        print(f"❌ 성과 지표 생성 실패: {result['message']}")
    
    # 5. 데이터 조회 테스트
    print("\n5. 데이터 조회 테스트")
    
    # 프로젝트 목록 조회
    projects = db_manager.get_projects()
    print(f"📁 프로젝트 수: {len(projects)}")
    
    # 인플루언서 목록 조회
    influencers = db_manager.get_influencers()
    print(f"👥 인플루언서 수: {len(influencers)}")
    
    # 프로젝트 인플루언서 조회
    project_influencers = db_manager.get_project_influencers(project_id)
    print(f"🔗 프로젝트-인플루언서 연결 수: {len(project_influencers)}")
    
    # 성과 지표 조회
    metrics = db_manager.get_performance_metrics(project_id, influencer_id)
    print(f"📊 성과 지표 수: {len(metrics)}")
    
    print("\n🎉 모든 테스트가 완료되었습니다!")

if __name__ == "__main__":
    # Supabase 설정 확인
    if not supabase_auth.is_authenticated():
        print("⚠️ 로그인이 필요합니다. 먼저 웹 애플리케이션에서 로그인해주세요.")
        print("💡 로그인 후 이 스크립트를 다시 실행하세요.")
    else:
        test_database_operations()
