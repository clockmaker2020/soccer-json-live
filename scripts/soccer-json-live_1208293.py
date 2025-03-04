import os
import json
import requests
import time
from datetime import datetime, timedelta, timezone

# ✅ API 설정
API_KEY = "0776a35eb1067086efe59bb7f93c6498"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io/fixtures"

# ✅ 저장할 폴더 설정
DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ✅ API 요청 함수
def fetch_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"🌐 API 응답 데이터: {json.dumps(data, indent=4, ensure_ascii=False)}")  # 응답 데이터 확인
        return data.get("response", [])
    except requests.exceptions.RequestException as e:
        print(f"⚠️ [ERROR] API 요청 실패: {e}")
        return []


# ✅ 경기 시작 시간 가져오기 (UTC → KST 변환)
def get_match_start_time(match_id):
    url = f"{BASE_URL}?id={match_id}"
    match_details = fetch_data(url)

    if not match_details:
        print(f"❌ 경기 {match_id} 정보를 가져올 수 없음.")
        return None

    match_data = match_details[0]
    fixture_info = match_data["fixture"]

    utc_time = datetime.strptime(fixture_info["date"], "%Y-%m-%dT%H:%M:%S%z")
    kst_time = utc_time.astimezone(timezone(timedelta(hours=9)))  # UTC+9 변환
    return kst_time

# ✅ 특정 경기 ID를 받아 실시간 데이터 수집
def get_match_data(match_id):
    url = f"{BASE_URL}?id={match_id}"
    match_details = fetch_data(url)
    
    if not match_details:
        print(f"❌ 경기 {match_id} 데이터를 가져올 수 없음.")
        return

    match_data = match_details[0]
    fixture_info = match_data["fixture"]
    teams = match_data["teams"]
    events = match_data.get("events", [])
    stats = match_data.get("statistics", [])
    league_info = match_data.get("league", {})

    # 🕒 UTC 시간 -> KST 시간 변환
    utc_time = datetime.strptime(fixture_info["date"], "%Y-%m-%dT%H:%M:%S%z")
    kst_time = utc_time.astimezone(timezone(timedelta(hours=9)))

    # 🏟 경기 개요 데이터
    overview_data = {
        "경기 ID": match_id,
        "경기 날짜": kst_time.strftime("%Y-%m-%d %H:%M"),
        "경기장": fixture_info["venue"]["name"],
        "도시": fixture_info["venue"]["city"],
        "경기 상태": fixture_info["status"]["long"],
        "리그": league_info.get("name", "N/A"),
        "라운드": league_info.get("round", "N/A"),
        "심판": fixture_info.get("referee", "N/A") or "N/A",
        "관중 수": fixture_info.get("attendance", "N/A") or "N/A"
    }

    # ⚽ 팀 정보 데이터
    teams_data = {
        "홈팀": {
            "이름": teams["home"]["name"],
            "로고": teams["home"]["logo"]
        },
        "원정팀": {
            "이름": teams["away"]["name"],
            "로고": teams["away"]["logo"]
        }
    }

    # 🔥 실시간 경기 정보
    live_data = {
        "현재 점수": f"{match_data['goals']['home']} - {match_data['goals']['away']}",
        "경기 상태": fixture_info["status"]["long"],
        "주요 경기 이벤트": [
            {
                "이벤트 종류": event.get("type", "N/A"),
                "선수": event.get("player", {}).get("name", "N/A"),
                "팀": event.get("team", {}).get("name", "N/A"),
                "시간": event.get("time", {}).get("elapsed", "N/A")
            }
            for event in events
        ],
        "경기 통계": [
            {
                "팀": stat["team"]["name"],
                "항목": stat["type"],
                "수치": stat["value"]
            }
            for stat in stats
        ]
    }

    # ✅ JSON 파일로 저장
    base_path = os.path.join(DATA_DIR, f"match_{match_id}")
    with open(f"{base_path}_overview.json", "w", encoding="utf-8") as f:
        json.dump(overview_data, f, ensure_ascii=False, indent=4)
    with open(f"{base_path}_teams.json", "w", encoding="utf-8") as f:
        json.dump(teams_data, f, ensure_ascii=False, indent=4)
    with open(f"{base_path}_live.json", "w", encoding="utf-8") as f:
        json.dump(live_data, f, ensure_ascii=False, indent=4)

    print(f"✅ 경기 {match_id} 개요 저장 완료: match_{match_id}_overview.json")
    print(f"✅ 경기 {match_id} 팀정보 저장 완료: match_{match_id}_teams.json")
    print(f"✅ 경기 {match_id} 실시간 저장 완료: match_{match_id}_live.json")

# ✅ 경기 시작 시간에 따른 업데이트 주기 결정
def determine_update_interval(match_id):
    now_kst = datetime.now(timezone(timedelta(hours=9)))  # 현재 KST 시간
    start_time_kst = get_match_start_time(match_id)

    if not start_time_kst:
        print(f"⚠️ 경기 {match_id}의 시작 시간을 가져올 수 없음.")
        return 10800  # 기본값: 3시간

    time_diff = (start_time_kst - now_kst).total_seconds()

    print(f"⏳ 현재 시간: {now_kst}, 경기 시작 시간: {start_time_kst}, 차이: {time_diff}초")

    # 잘못된 time_diff 값 필터링 (예: 경기 시간이 잘못되었거나 이미 종료된 경우)
    if time_diff < -86400:  # 경기 종료 후 하루가 지남
        print("🚫 경기 시간이 지나쳤음. 업데이트 중지.")
        return None

    # 경기 시작 전, 업데이트 주기 설정
    if time_diff > 86400:  # 경기 하루 전 (24시간 = 86400초)
        return 10800  # 3시간(10800초) 단위
    elif time_diff > 7200:  # 경기 당일 (2시간 초과)
        return 3600  # 1시간(3600초) 단위
    elif time_diff > 1200:  # 경기 시작 20분 전까지 (1200초 = 20분)
        return 300  # 5분(300초) 단위
    elif time_diff > 300:  # 경기 시작 5분 전까지 (300초 = 5분)
        return 60  # 1분(60초) 단위
    else:
        return 60  # 연장전 포함, 1분 유지




# ✅ 실행 루프
def run_update_loop(match_id):
    while True:
        interval = determine_update_interval(match_id)

        if interval is None:
            print("❌ 업데이트 주기 결정 실패. 프로그램 종료.")
            break

        get_match_data(match_id)
        print(f"🕒 {interval}초 후 데이터 업데이트 예정...")

        # 경기 종료 여부 확인
        match_details = fetch_data(f"{BASE_URL}?id={match_id}")
        if match_details:
            match_status = match_details[0]["fixture"]["status"]["long"]
            print(f"📌 현재 경기 상태: {match_status}")
            if match_status in ["Match Finished", "Cancelled", "Postponed"]:
                print("🏁 경기 종료됨. 업데이트 중단.")
                break

        # 중복 실행 방지
        if interval > 3600:  # 1시간 이상 업데이트 간격이 설정되면 GitHub Actions에서 실행되도록 종료
            print("⏹ 1시간 이상 주기 설정됨. GitHub Actions에서 실행하도록 중지.")
            break

        time.sleep(interval)


# ✅ 실행 (경기 ID 입력 필요)
if __name__ == "__main__":
    match_id = 1208293  # 원하는 경기 ID
    run_update_loop(match_id)
