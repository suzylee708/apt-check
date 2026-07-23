"""
550 Clinton Avenue 유닛 모니터링 스크립트
-------------------------------------------
Airtable 지원서 폼의 "Add unit" 드롭다운을 열어서 KEYWORD가 포함된
유닛이 새로 등록되었는지 확인하고, 발견되면 ntfy.sh로 푸시 알림을 보냅니다.

⚠️ 실행 전 반드시 확인할 것 (아래 "설정 방법" README 참고):
  1. 로컬에서 먼저 --debug 로 실행해서 실제 셀렉터가 맞는지 확인하세요.
     Airtable은 내부 클래스명이 랜덤 해시(class="xxxxx-yyyy")라서
     기본 셀렉터가 안 맞을 수 있습니다. 이 경우 DevTools로 실제
     구조를 확인 후 ADD_UNIT_BUTTON_TEXT / OPTION_SELECTOR 를 수정하세요.
"""

import os
import sys
from playwright.sync_api import sync_playwright
import requests

FORM_URL = "https://airtable.com/appsseXTOVx59HC0W/pagcVengefPFQvMZC/form"
KEYWORD = os.environ.get("KEYWORD", "550 Clinton")

# ntfy.sh 토픽 이름 (본인만 아는 임의의 문자열로 바꿔서 GitHub Secrets에 등록)
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")

# "Add unit" 버튼에 표시되는 텍스트 (스크린샷 기준)
ADD_UNIT_BUTTON_TEXT = "Add unit"

DEBUG = "--debug" in sys.argv


def log(*args):
    print(*args, flush=True)


def get_dropdown_options(page):
    """
    'Add unit' 버튼 클릭 후 열리는 드롭다운/리스트 안의 텍스트들을 모두 수집.
    Airtable 폼은 구조가 자주 바뀌므로, 여러 후보 셀렉터를 순서대로 시도합니다.
    """
    candidate_selectors = [
        "[role='option']",
        "[role='listbox'] *",
        "[role='dialog'] li",
        "[class*='listItem']",
        "[class*='list-item']",
        "[class*='option']",
    ]

    for selector in candidate_selectors:
        locator = page.locator(selector)
        count = locator.count()
        if count > 0:
            texts = locator.all_inner_texts()
            texts = [t.strip() for t in texts if t.strip()]
            if texts:
                log(f"[정보] 셀렉터 '{selector}' 로 {len(texts)}개 항목 발견")
                return texts

    # 위 후보들이 다 실패하면, 화면에 새로 뜬 팝업/다이얼로그 전체 텍스트를 통째로 반환
    log("[경고] 알려진 셀렉터로 항목을 찾지 못함. 전체 다이얼로그 텍스트로 대체합니다.")
    dialog = page.locator("[role='dialog'], [class*='popover'], [class*='dropdown']").first
    if dialog.count() > 0:
        return [dialog.inner_text()]
    return []


def check_units():
    matches = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not DEBUG)
        page = browser.new_page()
        page.goto(FORM_URL, wait_until="networkidle", timeout=30000)

        if DEBUG:
            page.screenshot(path="debug_1_loaded.png")

        # "Add unit" 버튼 클릭
        page.get_by_text(ADD_UNIT_BUTTON_TEXT, exact=False).first.click()
        page.wait_for_timeout(1500)

        if DEBUG:
            page.screenshot(path="debug_2_dropdown_open.png")

        # 드롭다운 리스트는 가상 스크롤(virtualized list)이라 화면에 보이는
        # 항목만 DOM에 렌더링됩니다. 스크롤 없이도 확인하기 위해,
        # 검색창에 KEYWORD를 직접 입력해 Airtable이 필터링하도록 합니다.
        search_box = page.get_by_placeholder("Search")
        search_box.fill(KEYWORD)
        page.wait_for_timeout(1200)

        if DEBUG:
            page.screenshot(path="debug_3_search_filtered.png")

        options = get_dropdown_options(page)

        log("--- 드롭다운에서 읽은 전체 텍스트 (총 %d개) ---" % len(options))
        for i, o in enumerate(options):
            log(f"[{i}] {repr(o)}")
        log("--------------------------------")

        text_blob = "\n".join(options)
        if KEYWORD.lower() in text_blob.lower():
            matches = [
                line.strip()
                for line in text_blob.split("\n")
                if KEYWORD.lower() in line.lower() and line.strip()
            ]

        browser.close()
    return matches


def notify(matches):
    if not NTFY_TOPIC:
        log("[경고] NTFY_TOPIC이 설정되지 않아 알림을 보내지 못했습니다.")
        return
    message = f"'{KEYWORD}' 유닛 발견!\n\n" + "\n".join(matches)
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": f"{KEYWORD} 유닛 등록됨!".encode("utf-8"),
                "Priority": "urgent",
                "Tags": "rotating_light,house",
            },
            timeout=10,
        )
        log("[알림 전송 완료]")
    except Exception as e:
        log(f"[에러] 알림 전송 실패: {e}")


if __name__ == "__main__":
    try:
        found = check_units()
    except Exception as e:
        log(f"[에러] 스크립트 실행 중 오류: {e}")
        sys.exit(1)

    if found:
        log("일치하는 유닛 발견:", found)
        notify(found)
    else:
        log(f"'{KEYWORD}' 포함된 유닛 없음. (정상 종료)")