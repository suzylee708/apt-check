# 550 Clinton Avenue 유닛 모니터링 봇 — 설정 가이드

## 개요
`check_units.py`가 정해진 시간마다 Airtable 지원서 폼을 열어서
"Add unit" 드롭다운에 "550 Clinton"이 포함된 유닛이 있는지 확인하고,
있으면 휴대폰으로 푸시 알림을 보냅니다. GitHub Actions가 무료로
정기 실행을 담당합니다.

---

## 1단계 — 로컬에서 먼저 테스트 (가장 중요)

Airtable 폼은 내부 구조(클래스명 등)가 자주 바뀌고, 랜덤 해시값이라
스크립트의 기본 셀렉터가 안 맞을 가능성이 있습니다. **반드시 로컬에서
먼저 디버그 모드로 실행해서 확인**하세요.

```bash
pip install playwright requests
playwright install chromium

python check_units.py --debug
```

`--debug` 모드는:
- 브라우저 창을 실제로 띄워서 눈으로 확인 가능
- `debug_1_loaded.png`, `debug_2_dropdown_open.png` 스크린샷 저장
- 드롭다운에서 읽어온 텍스트를 터미널에 전부 출력

**만약 "일치하는 유닛 없음"이 나왔는데 터미널에 출력된 텍스트 목록에
실제 유닛 이름들이 하나도 안 보인다면** → 셀렉터가 안 맞는 것입니다.
이 경우:
1. 폼 페이지에서 F12(개발자 도구) → "Add unit" 클릭 → 드롭다운 항목
   중 하나를 우클릭 → "검사(Inspect)"
2. 감싸고 있는 태그의 `role` 속성이나 클래스명 확인
3. `check_units.py`의 `candidate_selectors` 리스트에 그 셀렉터를
   맨 위에 추가

이 부분만 맞추면 나머지는 그대로 쓰시면 됩니다.

---

## 2단계 — ntfy.sh 알림 설정 (무료, 가입 불필요)

1. 휴대폰에 **ntfy** 앱 설치 (iOS/Android 둘 다 있음)
2. 앱에서 "Subscribe to topic" → 아무도 모를 만한 임의의 이름 입력
   (예: `suji-550clinton-a8f3k2`) — 이 이름을 아는 사람만 알림을
   구독/전송할 수 있으니 추측하기 어려운 이름으로 만드세요.
3. 이 토픽 이름을 기억해두세요 → 3단계에서 사용

테스트: 터미널에서 아래 명령으로 알림이 잘 오는지 확인
```bash
curl -d "테스트 알림입니다" ntfy.sh/여기에_본인_토픽이름
```

---

## 3단계 — GitHub 저장소에 배포

1. GitHub에 새 저장소 생성 (Private 추천)
2. 아래 두 파일을 저장소에 업로드:
   - `check_units.py` → 저장소 루트에
   - `check-units.yml` → 저장소 안에 `.github/workflows/check-units.yml` 경로로
     (폴더를 정확히 이 경로로 만들어야 합니다)
3. 저장소 Settings → Secrets and variables → Actions → "New repository secret"
   - Name: `NTFY_TOPIC`
   - Value: 2단계에서 만든 토픽 이름 (예: `suji-550clinton-a8f3k2`)
4. Actions 탭 → 워크플로우 선택 → "Run workflow" 버튼으로 수동 실행해서
   정상 작동하는지 먼저 확인
5. 이후엔 10분마다 자동 실행됩니다.

---

## 참고 / 주의사항

- **Private 저장소**: GitHub Actions 무료 사용량은 매달 2,000분입니다.
  10분마다 실행 시 한 달 약 4,300회 실행 → 각 실행이 1분 내외라면
  free tier를 넘을 수 있습니다. 넘으면 GitHub이 결제를 요구하거나
  워크플로우가 멈춥니다. 필요하면 간격을 20~30분으로 늘리세요
  (cron을 `*/20 * * * *` 등으로 수정).
- **Public 저장소**로 만들면 Actions 사용량이 무제한 무료입니다.
  코드 자체엔 민감한 정보가 없고 토픽 이름은 Secrets로 분리되어 있어서
  괜찮지만, 원치 않으면 Private + 간격 조정으로 가세요.
- GitHub Actions의 스케줄(cron)은 "정확히 그 시각"이 아니라 서버 상황에
  따라 몇 분 정도 늦게 실행될 수 있습니다. (완전 실시간은 아님)
- Airtable 폼 구조가 바뀌면 셀렉터를 다시 확인해야 할 수 있습니다.
  가끔 (예: 일주일에 한 번) `--debug`로 로컬 테스트를 다시 해보시는 걸
  권장합니다.
