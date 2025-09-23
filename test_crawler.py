#!/usr/bin/env python3
"""
Instagram 크롤러 테스트 스크립트
"""

from instagram_crawler import InstagramCrawler

def test_crawler():
    """크롤러 테스트"""
    print("Instagram 크롤러 테스트를 시작합니다...")
    
    # 테스트 URL (실제 Instagram 포스트 URL로 변경하세요)
    test_url = input("테스트할 Instagram URL을 입력하세요: ")
    
    if not test_url:
        print("URL이 입력되지 않았습니다.")
        return
    
    crawler = InstagramCrawler()
    
    try:
        print("크롤링을 시작합니다...")
        result = crawler.crawl_instagram_post(test_url, debug_mode=True)
        
        print("\n=== 크롤링 결과 ===")
        print(f"URL: {result['url']}")
        print(f"좋아요 수: {result['likes']}")
        print(f"댓글 수: {result['comments']}")
        print(f"상태: {result['status']}")
        
        if result['status'] != 'success':
            print(f"오류: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
    finally:
        crawler.close_driver()
        print("테스트가 완료되었습니다.")

if __name__ == "__main__":
    test_crawler()
