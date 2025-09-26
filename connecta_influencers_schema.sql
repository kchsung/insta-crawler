-- connecta_influencers 테이블 스키마 (참조용)
-- Supabase 데이터베이스의 실제 테이블 구조

create table public.connecta_influencers (
  id uuid not null default gen_random_uuid (),
  platform public.platform not null,
  content_category text not null,
  influencer_name text null default ''::text,
  sns_id text not null,
  sns_url text not null,
  contact_method public.contact_method not null default 'dm'::contact_method,
  followers_count bigint not null default 0,
  phone_number text null,
  kakao_channel_id text null,
  email text null,
  shipping_address text null,
  interested_products text[] null,
  owner_comment text null,
  manager_rating smallint null,
  content_rating smallint null,
  comments_count integer null default 0,
  foreign_followers_ratio numeric(5, 2) null,
  activity_score numeric(6, 2) null,
  preferred_mode public.influencer_pref null,
  price_krw numeric(14, 2) null,
  tags jsonb null,
  created_by uuid null default auth.uid (),
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  active boolean not null default true,
  post_count integer null default 0,
  profile_text text null,
  profile_image_url text null,
  constraint connecta_influencers_pkey primary key (id),
  constraint uq_platform_sns unique (platform, sns_id),
  constraint chk_content_rating_range check (
    (
      (
        (content_rating >= 1)
        and (content_rating <= 5)
      )
      or (content_rating is null)
    )
  ),
  constraint chk_followers_nonneg check ((followers_count >= 0)),
  constraint chk_influencer_name_nonempty check ((length(btrim(influencer_name)) > 0)),
  constraint chk_manager_rating_range check (
    (
      (
        (manager_rating >= 1)
        and (manager_rating <= 5)
      )
      or (manager_rating is null)
    )
  ),
  constraint chk_post_count_nonneg check ((post_count >= 0)),
  constraint chk_comments_nonneg check ((comments_count >= 0)),
  constraint chk_sns_id_nonempty check ((length(btrim(sns_id)) > 0)),
  constraint chk_url_nonempty check ((length(btrim(sns_url)) > 0)),
  constraint connecta_influencers_foreign_followers_ratio_check check (
    (
      (foreign_followers_ratio is null)
      or (
        (foreign_followers_ratio >= (0)::numeric)
        and (foreign_followers_ratio <= (100)::numeric)
      )
    )
  ),
  constraint connecta_influencers_price_krw_check check (
    (
      (price_krw is null)
      or (price_krw >= (0)::numeric)
    )
  ),
  constraint chk_profile_image_url_scheme check (
    (
      (profile_image_url is null)
      or (profile_image_url ~* '^https?://'::text)
    )
  ),
  constraint chk_content_category_nonempty check ((length(btrim(content_category)) > 0))
) TABLESPACE pg_default;

-- 인덱스들
create index IF not exists idx_connecta_influencers_category on public.connecta_influencers using btree (content_category) TABLESPACE pg_default;
create index IF not exists idx_connecta_influencers_pref on public.connecta_influencers using btree (preferred_mode) TABLESPACE pg_default;
create index IF not exists idx_connecta_influencers_active on public.connecta_influencers using btree (active) TABLESPACE pg_default;
create index IF not exists idx_connecta_influencers_name_trgm on public.connecta_influencers using gin (influencer_name gin_trgm_ops) TABLESPACE pg_default;
create index IF not exists idx_connecta_influencers_snsid_trgm on public.connecta_influencers using gin (sns_id gin_trgm_ops) TABLESPACE pg_default;
create index IF not exists idx_connecta_influencers_email_trgm on public.connecta_influencers using gin (email gin_trgm_ops) TABLESPACE pg_default;

-- 트리거
create trigger trg_connecta_influencers_updated_at BEFORE
update on connecta_influencers for EACH row
execute FUNCTION set_updated_at ();

-- 주요 필드 설명:
-- id: UUID 기본키
-- platform: 플랫폼 (instagram, youtube, tiktok, twitter 등)
-- content_category: 콘텐츠 카테고리 (필수)
-- influencer_name: 인플루언서 이름
-- sns_id: SNS ID (필수, unique with platform)
-- sns_url: SNS URL (필수)
-- followers_count: 팔로워 수
-- post_count: 게시물 수
-- profile_text: 프로필 텍스트
-- profile_image_url: 프로필 이미지 URL
-- active: 활성 상태
-- created_at, updated_at: 생성/수정 시간
