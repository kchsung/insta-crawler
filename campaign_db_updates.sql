-- 캠페인 DB 추가사항 적용
-- 1) campaigns 테이블 생성 (기존 테이블이 없는 경우)
-- 2) 컬럼 추가 (NULL 허용)
-- 3) 태그 검색 성능용 GIN 인덱스

-- 1) campaigns 테이블 생성 (기존 테이블이 없는 경우)
CREATE TABLE IF NOT EXISTS public.campaigns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_by UUID REFERENCES auth.users(id) NOT NULL,
    campaign_name TEXT NOT NULL,
    campaign_description TEXT,
    campaign_type TEXT NOT NULL CHECK (campaign_type IN ('seeding', 'promotion', 'sales')),
    start_date DATE NOT NULL,
    end_date DATE,
    status TEXT DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'paused', 'completed', 'canceled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2) 컬럼 추가 (NULL 허용)
ALTER TABLE public.campaigns
  ADD COLUMN IF NOT EXISTS campaign_instructions TEXT,  -- 캠페인 지시사항
  ADD COLUMN IF NOT EXISTS tags TEXT[];                 -- 관련 Tag정보(복수 태그)

-- 3) (선택) 태그 검색 성능용 GIN 인덱스
CREATE INDEX IF NOT EXISTS campaigns_tags_gin_idx
  ON public.campaigns USING gin (tags);

-- 4) 기타 필요한 인덱스들
CREATE INDEX IF NOT EXISTS idx_campaigns_created_by ON public.campaigns(created_by);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON public.campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON public.campaigns(created_at DESC);

-- 5) RLS (Row Level Security) 정책 설정
ALTER TABLE public.campaigns ENABLE ROW LEVEL SECURITY;

-- 캠페인 정책
CREATE POLICY "Users can view own campaigns" ON public.campaigns
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert own campaigns" ON public.campaigns
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update own campaigns" ON public.campaigns
    FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Users can delete own campaigns" ON public.campaigns
    FOR DELETE USING (auth.uid() = created_by);

-- 6) 업데이트 시간 트리거
CREATE TRIGGER update_campaigns_updated_at
    BEFORE UPDATE ON public.campaigns
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 7) 캠페인-인플루언서 연결 테이블 (기존 테이블이 없는 경우)
CREATE TABLE IF NOT EXISTS public.campaign_influencers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID REFERENCES public.campaigns(id) ON DELETE CASCADE,
    influencer_id UUID REFERENCES public.connecta_influencers(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'assigned' CHECK (status IN ('assigned', 'in_progress', 'completed', 'cancelled')),
    final_output_url TEXT,
    notes TEXT,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(campaign_id, influencer_id)
);

-- 8) 캠페인 인플루언서 참여 테이블 (기존 테이블이 없는 경우)
CREATE TABLE IF NOT EXISTS public.campaign_influencer_participations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID REFERENCES public.campaigns(id) ON DELETE CASCADE,
    influencer_id UUID REFERENCES public.connecta_influencers(id) ON DELETE CASCADE,
    manager_comment TEXT,
    influencer_requests TEXT,
    memo TEXT,
    sample_status TEXT DEFAULT '요청' CHECK (sample_status IN ('요청', '발송준비', '발송완료', '수령')),
    influencer_feedback TEXT,
    content_uploaded BOOLEAN DEFAULT FALSE,
    cost_krw DECIMAL(14,2) DEFAULT 0.0,
    content_links TEXT[],
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9) 성과 지표 테이블 (기존 테이블이 없는 경우)
CREATE TABLE IF NOT EXISTS public.performance_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID REFERENCES public.campaigns(id) ON DELETE CASCADE,
    influencer_id UUID REFERENCES public.connecta_influencers(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL CHECK (metric_type IN ('likes', 'comments', 'shares', 'views', 'clicks', 'conversions')),
    metric_value INTEGER DEFAULT 0,
    measurement_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10) 추가 인덱스들
CREATE INDEX IF NOT EXISTS idx_campaign_influencers_campaign_id ON public.campaign_influencers(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_influencers_influencer_id ON public.campaign_influencers(influencer_id);
CREATE INDEX IF NOT EXISTS idx_campaign_participations_campaign_id ON public.campaign_influencer_participations(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_participations_influencer_id ON public.campaign_influencer_participations(influencer_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_campaign_id ON public.performance_metrics(campaign_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_influencer_id ON public.performance_metrics(influencer_id);

-- 11) RLS 정책 설정 (캠페인 관련 테이블들)
ALTER TABLE public.campaign_influencers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaign_influencer_participations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_metrics ENABLE ROW LEVEL SECURITY;

-- 캠페인-인플루언서 정책
CREATE POLICY "Users can view own campaign influencers" ON public.campaign_influencers
    FOR SELECT USING (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

CREATE POLICY "Users can insert own campaign influencers" ON public.campaign_influencers
    FOR INSERT WITH CHECK (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

CREATE POLICY "Users can update own campaign influencers" ON public.campaign_influencers
    FOR UPDATE USING (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

CREATE POLICY "Users can delete own campaign influencers" ON public.campaign_influencers
    FOR DELETE USING (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

-- 캠페인 참여 정책
CREATE POLICY "Users can view own campaign participations" ON public.campaign_influencer_participations
    FOR SELECT USING (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

CREATE POLICY "Users can insert own campaign participations" ON public.campaign_influencer_participations
    FOR INSERT WITH CHECK (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

CREATE POLICY "Users can update own campaign participations" ON public.campaign_influencer_participations
    FOR UPDATE USING (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

CREATE POLICY "Users can delete own campaign participations" ON public.campaign_influencer_participations
    FOR DELETE USING (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

-- 성과 지표 정책
CREATE POLICY "Users can view own performance metrics" ON public.performance_metrics
    FOR SELECT USING (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

CREATE POLICY "Users can insert own performance metrics" ON public.performance_metrics
    FOR INSERT WITH CHECK (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

CREATE POLICY "Users can update own performance metrics" ON public.performance_metrics
    FOR UPDATE USING (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

CREATE POLICY "Users can delete own performance metrics" ON public.performance_metrics
    FOR DELETE USING (auth.uid() = (SELECT created_by FROM public.campaigns WHERE id = campaign_id));

-- 12) 업데이트 시간 트리거들
CREATE TRIGGER update_campaign_influencers_updated_at
    BEFORE UPDATE ON public.campaign_influencers
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_campaign_participations_updated_at
    BEFORE UPDATE ON public.campaign_influencer_participations
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_performance_metrics_updated_at
    BEFORE UPDATE ON public.performance_metrics
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
