name: Match Update

on:
  workflow_dispatch:
  schedule:
    - cron: "0 */6 * * *"  # 기본적으로 6시간마다 실행 (경기 전)

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
            MATCH_850_TIME=$(date -u -d "$MATCH_START -10 minutes" +"%Y-%m-%d %H:%M:%S")
            echo "MATCH_START=\"$MATCH_START\"" >> $GITHUB_ENV
            echo "MATCH_850_TIME=\"$MATCH_850_TIME\"" >> $GITHUB_ENV
          else
            echo "MATCH_START=UNKNOWN" >> $GITHUB_ENV
            echo "MATCH_850_TIME=UNKNOWN" >> $GITHUB_ENV
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

      - name: 현재 시간과 경기 시작 10분 전 시간 비교 후 업데이트 주기 결정
        id: update_schedule
        run: |
          CURRENT_TIME=$(date -u +"%Y-%m-%d %H:%M:%S")

          if [ "$MATCH_START" != "UNKNOWN" ] && [ "$MATCH_850_TIME" != "UNKNOWN" ]; then
            MATCH_START_TIME=$(date -u -d "$MATCH_START" +"%Y-%m-%d %H:%M:%S")
            MATCH_850_TIME_VAL=$(date -u -d "$MATCH_850_TIME" +"%Y-%m-%d %H:%M:%S")

            if [ "$CURRENT_TIME" \< "$MATCH_850_TIME_VAL" ]; then
              echo "UPDATE_INTERVAL=360" >> $GITHUB_ENV  # 6시간마다 (경기 전 10분 전까지)
            else
              echo "UPDATE_INTERVAL=1" >> $GITHUB_ENV  # 1분마다 (경기 시작 10분 전 이후)
            fi
          else
            echo "UPDATE_INTERVAL=360" >> $GITHUB_ENV  # 기본 6시간마다 업데이트
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
            echo "⏳ 경기 시작 10분 전 이후, 1분 간격 업데이트!"
          else
            echo "⌛ 경기 시작 10분 전 전까지, 6시간 간격 업데이트"
          fi
