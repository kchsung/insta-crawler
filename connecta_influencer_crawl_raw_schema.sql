-- connecta_influencer_crawl_raw 테이블 스키마
-- 크롤링 원시 데이터 저장용 테이블

CREATE TABLE public.connecta_influencer_crawl_raw (
  id uuid NOT NULL DEFAULT gen_random_uuid (),
  influencer_id uuid NOT NULL,
  platform public.platform NOT NULL,
  sns_id text NOT NULL,
  data_type public.crawl_data_type NOT NULL,
  raw_json jsonb NOT NULL,
  crawled_at timestamp with time zone NOT NULL DEFAULT now(),
  source_name text NULL,
  batch_id uuid NULL,
  content_hash text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT connecta_influencer_crawl_raw_pkey PRIMARY KEY (id),
  CONSTRAINT uq_crawl_dedupe UNIQUE (influencer_id, data_type, content_hash),
  CONSTRAINT connecta_influencer_crawl_raw_influencer_id_fkey FOREIGN KEY (influencer_id) REFERENCES connecta_influencers (id) ON DELETE CASCADE,
  CONSTRAINT fk_platform_sns_consistency CHECK ((length(btrim(sns_id)) > 0))
) TABLESPACE pg_default;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_crawl_influencer_type_time ON public.connecta_influencer_crawl_raw USING btree (influencer_id, data_type, crawled_at DESC) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_crawl_platform_sns_time ON public.connecta_influencer_crawl_raw USING btree (platform, sns_id, crawled_at DESC) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_crawl_rawjson_gin ON public.connecta_influencer_crawl_raw USING gin (raw_json) TABLESPACE pg_default;

-- 업데이트 시간 트리거
CREATE TRIGGER trg_crawl_raw_updated_at BEFORE
UPDATE ON connecta_influencer_crawl_raw FOR EACH ROW
EXECUTE FUNCTION set_updated_at ();

-- 테이블 설명
COMMENT ON TABLE public.connecta_influencer_crawl_raw IS '인플루언서 크롤링 원시 데이터 저장 테이블';
COMMENT ON COLUMN public.connecta_influencer_crawl_raw.influencer_id IS 'connecta_influencers 테이블의 인플루언서 ID';
COMMENT ON COLUMN public.connecta_influencer_crawl_raw.platform IS '플랫폼 (instagram, youtube, tiktok, twitter)';
COMMENT ON COLUMN public.connecta_influencer_crawl_raw.sns_id IS 'SNS 계정 ID';
COMMENT ON COLUMN public.connecta_influencer_crawl_raw.data_type IS '크롤링 데이터 타입 (profile, post, story 등)';
COMMENT ON COLUMN public.connecta_influencer_crawl_raw.raw_json IS '크롤링된 원시 JSON 데이터';
COMMENT ON COLUMN public.connecta_influencer_crawl_raw.crawled_at IS '크롤링 실행 시간';
COMMENT ON COLUMN public.connecta_influencer_crawl_raw.source_name IS '크롤링 소스명';
COMMENT ON COLUMN public.connecta_influencer_crawl_raw.batch_id IS '배치 크롤링 ID';
COMMENT ON COLUMN public.connecta_influencer_crawl_raw.content_hash IS '콘텐츠 해시 (중복 방지용)';
