# Instagram 크롤러 & 인플루언서 관리 시스템 📸

Instagram 포스트 크롤링과 인플루언서 프로젝트 관리를 위한 종합적인 Streamlit 웹 애플리케이션입니다.

## 🏗️ 프로젝트 구조

```
instrgram_crawler/
├── src/                    # 소스 코드
│   ├── ui/                 # UI 컴포넌트
│   │   ├── auth_components.py
│   │   ├── crawler_components.py
│   │   ├── project_components.py
│   │   └── __init__.py
│   ├── db/                 # 데이터베이스 관련
│   │   ├── models.py
│   │   ├── database.py
│   │   └── __init__.py
│   ├── supabase/           # Supabase 연동
│   │   ├── config.py
│   │   ├── auth.py
│   │   └── __init__.py
│   └── instagram_crawler.py # 크롤러 클래스
├── css/                    # 스타일시트
│   └── main.css
├── .streamlit/             # Streamlit 설정
│   ├── config.toml
│   └── secrets.toml.example
├── app.py                  # 메인 애플리케이션
├── requirements.txt        # 의존성
├── supabase_schema.sql     # 데이터베이스 스키마
└── README.md
```

## ✨ 주요 기능

### 🔐 사용자 인증
- Supabase Email Provider를 통한 회원가입/로그인
- 사용자별 데이터 격리
- 비밀번호 재설정 기능

### 🔍 단일 URL 크롤링
- 플랫폼 선택 (Instagram, YouTube, TikTok, Twitter)
- SNS ID 또는 URL 입력 방식 선택
- ❤️ 좋아요 수 추출
- 💬 댓글 수 추출
- 📊 결과를 표 형태로 표시
- 📥 CSV 파일로 다운로드
- 🗄️ 데이터베이스 자동 저장

### 📊 복수 URL 크롤링
- 데이터베이스에서 인플루언서 목록 선택
- 플랫폼별 필터링 기능
- 여러 인플루언서 자동 크롤링
- 실시간 진행률 표시
- 에러 처리 및 계속 진행
- 결과 통계 및 다운로드

### 📋 프로젝트 관리
- **프로젝트 생성**: 시딩, 홍보, 판매 프로젝트 생성
- **인플루언서 관리**: 플랫폼별 인플루언서 등록 및 관리
- **프로젝트-인플루언서 연결**: 프로젝트에 인플루언서 할당
- **진행상태 관리**: 할당, 진행중, 완료, 취소 상태 관리
- **최종 산출물 관리**: 완료된 작업의 URL 및 노트 관리

### 📈 성과 관리
- **프로젝트별 성과 현황**: 프로젝트 선택하여 성과 확인
- **인플루언서 성과 추적**: 개별 인플루언서의 성과 지표 관리
- **성과 크롤링**: 현재 구현된 크롤링 기능을 활용한 자동 성과 수집
- **성과 지표 입력**: 좋아요, 댓글, 공유, 조회수, 클릭수, 전환수 등
- **성과 히스토리**: 시간별 성과 추이 차트 및 데이터 표시

## 🚀 설치 및 실행

### 1. Supabase 프로젝트 설정

1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. `supabase_schema.sql` 파일의 내용을 Supabase SQL Editor에서 실행
   - Instagram 크롤링 관련 테이블
   - 프로젝트 관리 테이블 (projects, influencers, project_influencers)
   - 성과 관리 테이블 (performance_metrics)
   - RLS (Row Level Security) 정책 설정
3. Authentication > Settings에서 Email Provider 활성화

### 2. 환경 변수 설정

#### 로컬 개발
```bash
# env.example을 .env로 복사
cp env.example .env

# .env 파일에 Supabase 정보 입력
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

#### Streamlit Cloud 배포
1. Streamlit Cloud에서 Secrets 설정
2. `.streamlit/secrets.toml.example`을 참고하여 secrets 설정

### 3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 애플리케이션 실행

```bash
streamlit run app.py
```

### 5. 브라우저에서 확인

애플리케이션이 실행되면 자동으로 브라우저가 열리고 `http://localhost:8501`에서 확인할 수 있습니다.

## 사용 방법

### 🔍 단일 URL 크롤링
1. **플랫폼 선택**: Instagram, YouTube, TikTok, Twitter 중 선택
2. **입력 방식 선택**: SNS ID 또는 URL 입력 방식 선택
3. **정보 입력**: 
   - SNS ID: `@username` 또는 `username` 형식
   - URL: 해당 플랫폼의 프로필 또는 포스트 URL
4. **크롤링 시작**: "크롤링 시작" 버튼을 클릭
5. **결과 확인**: 좋아요 수와 댓글 수가 표시됩니다

### 📊 복수 URL 크롤링
1. **플랫폼 필터**: 크롤링할 플랫폼을 선택 (전체 또는 특정 플랫폼)
2. **인플루언서 선택**: 데이터베이스에서 크롤링할 인플루언서를 다중 선택
3. **크롤링 시작**: "일괄 크롤링 시작" 버튼을 클릭
4. **진행률 확인**: 실시간으로 진행률과 상태를 확인
5. **결과 다운로드**: 완료 후 CSV 파일로 결과를 다운로드

### 📋 프로젝트 관리
1. **프로젝트 생성**: 
   - 프로젝트 이름, 유형(시딩/홍보/판매), 설명 입력
   - 상태 설정 (진행중/완료/취소)
2. **인플루언서 등록**:
   - 플랫폼, SNS ID, 표시 이름, 팔로워 수, 참여율 등 입력
3. **프로젝트-인플루언서 연결**: 프로젝트에 인플루언서 할당
4. **진행상태 관리**: 할당된 인플루언서의 작업 상태 업데이트

### 📈 성과 관리
1. **프로젝트 선택**: 성과를 확인할 프로젝트 선택
2. **성과 크롤링**: 인플루언서의 현재 성과를 자동으로 크롤링
3. **성과 입력**: 수동으로 성과 지표 입력 (좋아요, 댓글, 공유 등)
4. **성과 분석**: 시간별 성과 추이 차트 및 상세 데이터 확인

## 지원하는 데이터 형식

- **숫자**: 1,234
- **K 단위**: 1.2K (1,200으로 변환)
- **M 단위**: 1.5M (1,500,000으로 변환)

## 주의사항

⚠️ **중요**: 이 도구는 교육 및 연구 목적으로만 사용하세요.

- Instagram의 이용약관을 준수해야 합니다
- 과도한 요청은 계정 제재를 받을 수 있습니다
- 비공개 계정의 포스트는 접근할 수 없습니다
- Instagram의 정책 변경에 따라 작동하지 않을 수 있습니다

## 기술 스택

- **Streamlit**: 웹 애플리케이션 프레임워크
- **Supabase**: 백엔드 데이터베이스 및 인증
- **Selenium**: 웹 브라우저 자동화
- **Chrome WebDriver**: 브라우저 드라이버
- **BeautifulSoup**: HTML 파싱
- **Pandas**: 데이터 처리
- **Pydantic**: 데이터 모델링

## 문제 해결

### Chrome 드라이버 오류
- Chrome 브라우저가 설치되어 있는지 확인하세요
- `webdriver-manager`가 자동으로 드라이버를 다운로드합니다

### 크롤링 실패
- URL이 올바른지 확인하세요
- 포스트가 공개되어 있는지 확인하세요
- 네트워크 연결을 확인하세요

## 라이선스

이 프로젝트는 교육 목적으로만 사용되어야 하며, 상업적 사용은 권장하지 않습니다.
