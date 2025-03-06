name: Match Update

on:
  workflow_dispatch:
  schedule:
    - cron: "*/10 * * * *"  # 기본적으로 10분마다 실행 (초기 상태)

jobs:
  update-match:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # ✅ 푸시 권한 활성화

    steps:
      - name: 저장소 체크아웃
        uses: actions/checkout@v3
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Python 설정
        uses: actions/setup-python@v3
        with:
          python-version: "3.9"

      - name: 의존성 설치
        run: pip install -r requirements.txt

      - name: 환경 변수 로드 (GitHub Secrets 사용)
        env:
          API_KEY: ${{ secrets.API_KEY }}
        run: echo "API_KEY=${API_KEY}" > .env

      - name: 경기 시작 시간 확인
        id: check_start_time
        run: |
          if [ -f "data/match_1208293_start.json" ]; then
            MATCH_START=$(jq -r '.start_time' data/match_1208293_start.json)
            echo "MATCH_START=\"$MATCH_START\"" >> $GITHUB_ENV
          else
            echo "MATCH_START=UNKNOWN" >> $GITHUB_ENV
          fi

      - name: 이전 경기 상태 확인
        id: check_status
        run: |
          if [ -f "data/match_1208293_status.json" ]; then
            MATCH_STATUS=$(jq -r '.status' data/match_1208293_status.json)
            echo "MATCH_STATUS=\"$MATCH_STATUS\"" >> $GITHUB_ENV
          else
            echo "MATCH_STATUS=UNKNOWN" >> $GITHUB_ENV
          fi

      - name: 경기 시작 10분 전인지 확인 후 업데이트 주기 조정
        id: update_schedule
        run: |
          if [ "$MATCH_START" != "UNKNOWN" ]; then
            CURRENT_TIME=$(date -u +"%Y-%m-%d %H:%M:%S")
            MATCH_START_TIME=$(date -u -d "$MATCH_START" +"%Y-%m-%d %H:%M:%S")
            TIME_DIFF=$(( $(date -d "$MATCH_START_TIME" +%s) - $(date -d "$CURRENT_TIME" +%s) ))
            
            if [ $TIME_DIFF -le 600 ] && [ $TIME_DIFF -gt 0 ]; then
              echo "UPDATE_INTERVAL=1" >> $GITHUB_ENV
            else
              echo "UPDATE_INTERVAL=10" >> $GITHUB_ENV
            fi
          else
            echo "UPDATE_INTERVAL=10" >> $GITHUB_ENV
          fi

      - name: 경기 데이터 업데이트
        id: match
        if: env.MATCH_STATUS != 'STOP'
        run: python scripts/soccer-json-live_1208293.py

      - name: 경기 종료 또는 연기 확인
        if: env.MATCH_STATUS == 'STOP'
        run: echo "🏁 경기 종료 또는 연기됨. 업데이트 중지."

      - name: 변경 사항 커밋 및 푸시
        if: env.MATCH_STATUS != 'STOP'
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions@users.noreply.github.com"
          git add data/match_1208293_*.json
          git commit -m "🔄 자동 업데이트: 경기 데이터 갱신" || echo "No changes to commit"
          git push origin HEAD:${{ github.ref }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: 경기 상태에 따라 Actions 업데이트 주기 변경
        if: env.MATCH_STATUS != 'STOP'
        run: |
          if [ "$UPDATE_INTERVAL" == "1" ]; then
            echo "⏳ 경기 시작 10분 전, 1분 간격 업데이트!"
          else
            echo "⌛ 기본 10분 간격 업데이트"
          fi
