-- Instagram 크롤러 데이터베이스 스키마
-- Supabase에서 실행할 SQL 스크립트
-- 기존 connecta_influencers와 connecta_influencer_crawl_raw 테이블 활용

-- Instagram 크롤링 세션 테이블 (기존 테이블과 별도로 관리)
CREATE TABLE IF NOT EXISTS instagram_crawl_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    session_name TEXT NOT NULL,
    total_posts INTEGER DEFAULT 0,
    successful_posts INTEGER DEFAULT 0,
    failed_posts INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Instagram 포스트 크롤링 결과 테이블 (기존 테이블과 별도로 관리)
CREATE TABLE IF NOT EXISTS instagram_crawl_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    session_id UUID REFERENCES instagram_crawl_sessions(id),
    post_name TEXT NOT NULL,
    post_url TEXT NOT NULL,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'error', 'timeout')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_instagram_crawl_sessions_user_id ON instagram_crawl_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_instagram_crawl_sessions_created_at ON instagram_crawl_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_instagram_crawl_results_user_id ON instagram_crawl_results(user_id);
CREATE INDEX IF NOT EXISTS idx_instagram_crawl_results_session_id ON instagram_crawl_results(session_id);
CREATE INDEX IF NOT EXISTS idx_instagram_crawl_results_created_at ON instagram_crawl_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_instagram_crawl_results_status ON instagram_crawl_results(status);

-- RLS (Row Level Security) 정책 설정
ALTER TABLE instagram_crawl_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE instagram_crawl_results ENABLE ROW LEVEL SECURITY;

-- Instagram 크롤링 세션 정책
CREATE POLICY "Users can view own crawl sessions" ON instagram_crawl_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own crawl sessions" ON instagram_crawl_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own crawl sessions" ON instagram_crawl_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- Instagram 크롤링 결과 정책
CREATE POLICY "Users can view own crawl results" ON instagram_crawl_results
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own crawl results" ON instagram_crawl_results
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own crawl results" ON instagram_crawl_results
    FOR UPDATE USING (auth.uid() = user_id);

-- 업데이트 시간 자동 갱신 함수
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 업데이트 시간 트리거
CREATE TRIGGER update_instagram_crawl_sessions_updated_at
    BEFORE UPDATE ON instagram_crawl_sessions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_instagram_crawl_results_updated_at
    BEFORE UPDATE ON instagram_crawl_results
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Instagram 크롤링 통계 뷰 생성
CREATE OR REPLACE VIEW instagram_crawl_stats AS
SELECT 
    au.id as user_id,
    au.email,
    COUNT(DISTINCT ics.id) as total_sessions,
    COUNT(DISTINCT icr.id) as total_posts,
    SUM(CASE WHEN icr.status = 'success' THEN 1 ELSE 0 END) as successful_posts,
    SUM(CASE WHEN icr.status = 'error' THEN 1 ELSE 0 END) as failed_posts,
    SUM(CASE WHEN icr.status = 'success' THEN icr.likes ELSE 0 END) as total_likes,
    SUM(CASE WHEN icr.status = 'success' THEN icr.comments ELSE 0 END) as total_comments,
    MAX(ics.created_at) as last_crawl_date
FROM auth.users au
LEFT JOIN instagram_crawl_sessions ics ON au.id = ics.user_id
LEFT JOIN instagram_crawl_results icr ON au.id = icr.user_id
GROUP BY au.id, au.email;

-- 뷰에 대한 RLS 정책
ALTER VIEW instagram_crawl_stats SET (security_invoker = true);

-- 프로젝트 관리 테이블
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    project_name TEXT NOT NULL,
    project_type TEXT NOT NULL CHECK (project_type IN ('seeding', 'promotion', 'sales')),
    description TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인플루언서 테이블
CREATE TABLE IF NOT EXISTS influencers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('instagram', 'youtube', 'tiktok', 'twitter')),
    sns_id TEXT NOT NULL,
    display_name TEXT,
    profile_url TEXT,
    follower_count INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, platform, sns_id)
);

-- 비로그인 사용자를 위한 임시 인플루언서 테이블
CREATE TABLE IF NOT EXISTS anonymous_influencers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,  -- 세션별 고유 ID
    platform TEXT NOT NULL CHECK (platform IN ('instagram', 'youtube', 'tiktok', 'twitter')),
    sns_id TEXT NOT NULL,
    display_name TEXT,
    profile_url TEXT,
    follower_count INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, platform, sns_id)
);

-- 프로젝트-인플루언서 연결 테이블
CREATE TABLE IF NOT EXISTS project_influencers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    influencer_id UUID REFERENCES influencers(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'assigned' CHECK (status IN ('assigned', 'in_progress', 'completed', 'cancelled')),
    final_output_url TEXT,
    notes TEXT,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, influencer_id)
);

-- 성과 관리 테이블
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    influencer_id UUID REFERENCES influencers(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL CHECK (metric_type IN ('likes', 'comments', 'shares', 'views', 'clicks', 'conversions')),
    metric_value INTEGER DEFAULT 0,
    measurement_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(project_type);
CREATE INDEX IF NOT EXISTS idx_influencers_user_id ON influencers(user_id);
CREATE INDEX IF NOT EXISTS idx_influencers_platform ON influencers(platform);
CREATE INDEX IF NOT EXISTS idx_anonymous_influencers_session_id ON anonymous_influencers(session_id);
CREATE INDEX IF NOT EXISTS idx_anonymous_influencers_platform ON anonymous_influencers(platform);
CREATE INDEX IF NOT EXISTS idx_project_influencers_project_id ON project_influencers(project_id);
CREATE INDEX IF NOT EXISTS idx_project_influencers_influencer_id ON project_influencers(influencer_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_project_id ON performance_metrics(project_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_influencer_id ON performance_metrics(influencer_id);

-- RLS 정책 설정
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE influencers ENABLE ROW LEVEL SECURITY;
ALTER TABLE anonymous_influencers ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_influencers ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;

-- 프로젝트 정책
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own projects" ON projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (auth.uid() = user_id);

-- 인플루언서 정책
CREATE POLICY "Users can view own influencers" ON influencers
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own influencers" ON influencers
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own influencers" ON influencers
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own influencers" ON influencers
    FOR DELETE USING (auth.uid() = user_id);

-- 비로그인 사용자 인플루언서 정책 (모든 사용자 접근 허용)
CREATE POLICY "Anyone can view anonymous influencers" ON anonymous_influencers
    FOR SELECT USING (true);
CREATE POLICY "Anyone can insert anonymous influencers" ON anonymous_influencers
    FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update anonymous influencers" ON anonymous_influencers
    FOR UPDATE USING (true);
CREATE POLICY "Anyone can delete anonymous influencers" ON anonymous_influencers
    FOR DELETE USING (true);

-- 프로젝트-인플루언서 정책
CREATE POLICY "Users can view own project influencers" ON project_influencers
    FOR SELECT USING (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));
CREATE POLICY "Users can insert own project influencers" ON project_influencers
    FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));
CREATE POLICY "Users can update own project influencers" ON project_influencers
    FOR UPDATE USING (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));
CREATE POLICY "Users can delete own project influencers" ON project_influencers
    FOR DELETE USING (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));

-- 성과 지표 정책
CREATE POLICY "Users can view own performance metrics" ON performance_metrics
    FOR SELECT USING (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));
CREATE POLICY "Users can insert own performance metrics" ON performance_metrics
    FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));
CREATE POLICY "Users can update own performance metrics" ON performance_metrics
    FOR UPDATE USING (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));
CREATE POLICY "Users can delete own performance metrics" ON performance_metrics
    FOR DELETE USING (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));

-- 업데이트 시간 트리거
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_influencers_updated_at
    BEFORE UPDATE ON influencers
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_project_influencers_updated_at
    BEFORE UPDATE ON project_influencers
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_performance_metrics_updated_at
    BEFORE UPDATE ON performance_metrics
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();