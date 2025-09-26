from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class InstagramCrawlResult(BaseModel):
    """Instagram 크롤링 결과 데이터 모델"""
    id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    post_name: str
    post_url: str
    likes: int = 0
    comments: int = 0
    status: str = "pending"  # pending, success, error, timeout
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class InstagramCrawlSession(BaseModel):
    """Instagram 크롤링 세션 데이터 모델"""
    id: Optional[str] = None
    user_id: Optional[str] = None
    session_name: str
    total_posts: int = 0
    successful_posts: int = 0
    failed_posts: int = 0
    status: str = "running"  # running, completed, failed
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserStats(BaseModel):
    """사용자 통계 데이터 모델"""
    user_id: str
    email: str
    total_sessions: int = 0
    total_posts: int = 0
    successful_posts: int = 0
    failed_posts: int = 0
    total_likes: int = 0
    total_comments: int = 0
    last_crawl_date: Optional[datetime] = None

class Campaign(BaseModel):
    """캠페인 데이터 모델"""
    id: Optional[str] = None
    created_by: Optional[str] = None
    campaign_name: str
    campaign_description: Optional[str] = None
    campaign_type: str  # seeding, promotion, sales
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "planned"  # planned, active, paused, completed, canceled
    campaign_instructions: Optional[str] = None  # 캠페인 지시사항
    tags: Optional[List[str]] = None  # 관련 Tag정보(복수 태그)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Influencer(BaseModel):
    """인플루언서 데이터 모델"""
    id: Optional[str] = None
    user_id: Optional[str] = None
    platform: str  # instagram, youtube, tiktok, twitter
    sns_id: str
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    follower_count: int = 0
    engagement_rate: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CampaignInfluencer(BaseModel):
    """캠페인-인플루언서 연결 데이터 모델"""
    id: Optional[str] = None
    campaign_id: str
    influencer_id: str
    status: str = "assigned"  # assigned, in_progress, completed, cancelled
    final_output_url: Optional[str] = None
    notes: Optional[str] = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CampaignInfluencerParticipation(BaseModel):
    """캠페인 인플루언서 참여 데이터 모델"""
    id: Optional[str] = None
    campaign_id: str
    influencer_id: str
    manager_comment: Optional[str] = None
    influencer_requests: Optional[str] = None
    memo: Optional[str] = None
    sample_status: str = "요청"  # 요청, 발송준비, 발송완료, 수령
    influencer_feedback: Optional[str] = None
    content_uploaded: bool = False
    cost_krw: float = 0.0
    content_links: List[str] = []
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PerformanceMetric(BaseModel):
    """성과 지표 데이터 모델"""
    id: Optional[str] = None
    campaign_id: str
    influencer_id: str
    metric_type: str  # likes, comments, shares, views, clicks, conversions
    metric_value: int = 0
    measurement_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None