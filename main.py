import json
import os
import requests
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
DATA_FILE = "movies.json"
CGV_URL = "http://www.cgv.co.kr/movies/?ft=0"

def fetch_cgv_movies():
    movies = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(CGV_URL, wait_until="domcontentloaded", timeout=60000)
            titles = page.locator(".sect-movie-chart .title").all_inner_texts()

            for title in titles:
                cleaned_title = title.strip()
                if cleaned_title and cleaned_title not in movies:
                    movies.append(cleaned_title)
        except Exception as e:
            print(f"크롤링 오류: {e}")
        finally:
            browser.close()

    return movies

def load_previous_movies():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"데이터 로드 실패: {e}")
    return set()

def save_current_movies(movies_set):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(movies_set), f, ensure_ascii=False, indent=2)

def send_discord_notification(new_movies):
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")
        return

    movie_list_str = "\n".join([f"• **{movie}**" for movie in new_movies])
    message = {
        "embeds": [
            {
                "title": "🎬 CGV 신규 영화 등록 알림",
                "description": f"CGV 상영 차트에 새 영화가 추가되었습니다!\n\n{movie_list_str}",
                "color": 15158332,
                "footer": {"text": "CGV Watcher Bot"},
            }
        ]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=message)

def main():
    print("CGV 영화 목록 확인 중...")
    current_movies = fetch_cgv_movies()

    if not current_movies:
        print("영화 목록을 가져올 수 없습니다.")
        return

    current_set = set(current_movies)
    previous_set = load_previous_movies()

    new_movies = current_set - previous_set

    if new_movies:
        print(f"새 영화 발견: {new_movies}")
        send_discord_notification(list(new_movies))
        save_current_movies(previous_set | new_movies)
    else:
        print("새로운 영화가 없습니다.")

    if not os.path.exists(DATA_FILE):
        save_current_movies(current_set)

if __name__ == "__main__":
    main()
