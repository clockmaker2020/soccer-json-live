import os
import json
import requests
from datetime import datetime, timedelta

# ✅ API 설정
API_KEY = "0776a35eb1067086efe59bb7f93c6498"
HEADERS = {"x-apisports-key": API_KEY}

# ✅ 저장할 폴더 설정 (GitHub 환경에 맞게 변경)
DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)


# ✅ API 요청 함수
def fetch_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("response", [])
    except requests.exceptions.RequestException:
        return []

# ✅ 특정 경기 ID를 받아 실시간 데이터 수집
def get_match_data(match_id):
    detail_url = f"https://v3.football.api-sports.io/fixtures?id={match_id}"
    odds_url = f"https://v3.football.api-sports.io/odds?fixture={match_id}"
    
    match_details = fetch_data(detail_url)
    odds_details = fetch_data(odds_url)
    
    if not match_details:
        return
    
    match_data = match_details[0]
    fixture_info = match_data["fixture"]
    teams = match_data["teams"]
    events = match_data.get("events", [])
    stats = match_data.get("statistics", [])
    lineups = match_data.get("lineups", [])
    players = match_data.get("players", [])
    league_info = match_data.get("league", {})

    # 🕒 UTC 시간 -> KST 시간 변환
    utc_time = datetime.strptime(fixture_info["date"], "%Y-%m-%dT%H:%M:%S%z")
    kst_time = utc_time + timedelta(hours=9)

    # 🎲 배당률 데이터
    odds_data = []
    if odds_details:
        for bookmaker in odds_details:
            for bet in bookmaker.get("bookmakers", []):
                odds_entry = {
                    "배팅사": bet.get("name", "N/A"),
                    "배당률": []
                }
                for market in bet.get("bets", []):
                    for o in market.get("values", []):
                        odds_entry["배당률"].append({
                            "종류": o.get("name", "N/A"),
                            "배당": o.get("value", "N/A")
                        })
                odds_data.append(odds_entry)


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

    status_file = os.path.join(DATA_DIR, f"match_{match_id}_status.json")
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(match_status_data, f, ensure_ascii=False, indent=4)

    start_file = os.path.join(DATA_DIR, f"match_{match_id}_start.json")
    with open(start_file, "w", encoding="utf-8") as f:
        json.dump(match_start_data, f, ensure_ascii=False, indent=4)



    
    # 🔥 실시간 경기 정보
    live_data = {
        "현재 점수": f"{match_data['goals']['home']} - {match_data['goals']['away']}",
        "경기 상태": fixture_info["status"]["long"],
        "득점 기록": [
            {
                "시간": event["time"]["elapsed"],
                "선수": event["player"]["name"],
                "팀": event["team"]["name"]
            }
            for event in events if event["type"] == "Goal"
        ],
        
        "주요 경기 이벤트": [
            {
                "이벤트 종류": event["type"],
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
        ],
        
        "선수 명단 및 라인업": [
            {
                "팀": lineup["team"]["name"],
                "포메이션": lineup["formation"],
                "선발 선수": [player["player"]["name"] for player in lineup["startXI"]],
                "교체 선수": [player["player"]["name"] for player in lineup["substitutes"]]
            }
            for lineup in lineups
        ],
        
        "선수별 통계": [
            {
                "선수": player["player"]["name"],
                "팀": player["team"]["name"],
                "포지션": player["player"]["position"],
                "스탯": player["statistics"]
            }
            for team in players for player in team["players"]
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
    print(f"✅ 경기 {match_id} 팀 정보 저장 완료: match_{match_id}_teams.json")
    print(f"✅ 경기 {match_id} 실시간 경기 데이터 저장 완료: match_{match_id}_live.json")
    print(f"✅ 경기 {match_id} 상태 저장 완료: match_{match_id}_status.json")
    print(f"✅ 경기 {match_id} 시작 시간 저장 완료: match_{match_id}_start.json")
    
    
# ✅ 실행 (경기 ID 입력 필요)
if __name__ == "__main__":
    match_id = 1208293  # 원하는 경기 ID로 변경
    get_match_data(match_id)
