document.addEventListener("DOMContentLoaded", function () {
    let matchId = "1208293";
    let baseUrl = "https://clockmaker2020.github.io/soccer-json-live/data/";

    let urls = {
        "overview": `${baseUrl}match_${matchId}_overview.json`,
        "teams": `${baseUrl}match_${matchId}_teams.json`,
        "odds": `${baseUrl}match_${matchId}_odds.json`,
        "h2h": `${baseUrl}match_${matchId}_h2h.json`,
        "injuries": `${baseUrl}match_${matchId}_injuries.json`,
        "live": `${baseUrl}match_${matchId}_live.json`
    };

    function fetchJson(url) {
        return fetch(url)
            .then(response => response.ok ? response.json() : Promise.reject(`HTTP 오류: ${response.status}`))
            .catch(error => {
                console.error(`❌ JSON 로드 실패: ${url}`, error);
                return null;
            });
    }

    function setElementText(id, text) {
        let element = document.getElementById(id);
        if (element) element.innerHTML = text || "데이터 없음";
    }

    function setElementImage(id, src) {
        let element = document.getElementById(id);
        if (element) element.src = src;
    }

    function loadMatchData() {
        Promise.all([
            fetchJson(urls["overview"]),
            fetchJson(urls["teams"]),
            fetchJson(urls["odds"]),
            fetchJson(urls["h2h"]),
            fetchJson(urls["injuries"])
        ]).then(([overview, teams, odds, h2h, injuries]) => {
            if (!overview || !teams || !odds || !h2h || !injuries) {
                console.warn("⚠️ 일부 JSON 파일이 로드되지 않았습니다.");
                return;
            }

            // 📌 1. 경기 개요 데이터 적용
            if (overview) {
                setElementText("match-date", overview["경기 날짜"] || "날짜 정보 없음");
                setElementText("stadium", overview["경기장"] || "경기장 정보 없음");
                setElementText("city", overview["도시"] || "도시 정보 없음");
                setElementText("match-status", overview["경기 상태"] || "경기 상태 없음");
                setElementText("league", overview["리그"] || "리그 정보 없음");
                setElementText("round", overview["라운드"] || "라운드 정보 없음");
                setElementText("referee", overview["심판"] || "심판 정보 없음");
                setElementText("attendance", overview["관중 수"] || "관중 정보 없음");
            }

            // 📌 2. 팀 정보 적용
            if (teams) {
                setElementText("home-team", teams["홈팀"]["이름"] || "홈팀 없음");
                setElementText("away-team", teams["원정팀"]["이름"] || "원정팀 없음");
                setElementImage("home-logo", teams["홈팀"]["로고"] || "");
                setElementImage("away-logo", teams["원정팀"]["로고"] || "");
            }

            // 📌 3. 배당률 정보 적용
            if (odds) {
                setElementText("home-odds", odds["홈 승리 확률"] || "배당률 없음");
                setElementText("draw-odds", odds["무승부 확률"] || "배당률 없음");
                setElementText("away-odds", odds["원정 승리 확률"] || "배당률 없음");
            }

            console.log("✅ 경기 기본 정보 업데이트 완료");
        });
    }

    loadMatchData();

    // ✅ 실시간 경기 데이터 가져오기
    function fetchLiveData() {
        fetchJson(urls["live"]).then(liveData => {
            if (!liveData) {
                console.warn("⚠️ 실시간 데이터 없음");
                return;
            }

            console.log("✅ 실시간 경기 데이터 로드 성공:", liveData);

            // ✅ 경기 점수
            let score = liveData["현재 점수"] || "⚽ 경기 시작 전";
            let goals = liveData["득점 기록"] || [];
            let events = liveData["주요 경기 이벤트"] || [];
            let statistics = liveData["경기 통계"] || [];

            let liveScoreElement = document.getElementById("live-score");
            let goalRecordElement = document.getElementById("goal-record");
            let matchEventsElement = document.getElementById("match-events");

            // ✅ 득점 기록 변환
            let goalText = goals.length > 0 ? goals.map(g => `⚽ ${g}`).join("<br>") : "득점 없음";

            // ✅ 주요 경기 이벤트 변환
            let eventText = events.length > 0 ? events.map(e => `📢 ${e}`).join("<br>") : "주요 이벤트 없음";

            // ✅ 경기 통계 변환 (예: 점유율, 슈팅 수 등)
            let statsText = statistics.length > 0
                ? statistics.map(stat => `${stat["팀"]}: ${stat["항목"]} - ${stat["수치"]}`).join("<br>")
                : "경기 통계 없음";

            // ✅ HTML 업데이트
            liveScoreElement.innerHTML = score;
            goalRecordElement.innerHTML = goalText;
            matchEventsElement.innerHTML = eventText;

            console.log("✅ 실시간 경기 정보 업데이트 완료", liveData);
        }).catch(error => {
            console.error("❌ 실시간 경기 정보 로드 실패:", error);
        });
    }

    // ✅ 사용자가 버튼을 클릭했을 때만 실시간 데이터 불러오기
    let updateButton = document.getElementById("update-button");
    updateButton.addEventListener("click", function () {
        console.log("✅ 준실시간 업데이트 버튼 클릭됨: 실시간 데이터 불러오기 시작");
        fetchLiveData();
        updateButton.style.backgroundColor = "#90EE90"; // 옅은 녹색으로 버튼 변경
        setTimeout(() => updateButton.style.backgroundColor = "#FFC0CB", 5000); // 5초 후 원래 색상 복귀
    });
});
