import json
import os
import re
import urllib.request
from collections import Counter

# 설정
# 스크립트 파일(scripts/update_service.py) 위치를 기준으로 프로젝트 루트 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_URL = "https://smok95.github.io/lotto/results/all.json"
HISTORY_PATH = os.path.join(BASE_DIR, "data", "lotto_history.json")
HTML_PATH = os.path.join(BASE_DIR, "index.html")

def update_service():
    print("--- 로또 서비스 주간 자동 업데이트 시작 ---")
    
    # 1. 데이터 다운로드
    try:
        print(f"1. 최신 데이터 다운로드 중: {DATA_URL}")
        with urllib.request.urlopen(DATA_URL) as response:
            all_data = json.loads(response.read().decode())
        
        cleaned_data = [{"draw_no": d["draw_no"], "numbers": d["numbers"]} for d in all_data]
        latest_draw = cleaned_data[-1]["draw_no"]
        
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        print(f"   => {latest_draw}회차까지 저장 완료.")
    except Exception as e:
        print(f"Error (Download): {e}")
        return

    # 2. 데이터 분석
    print("2. 전수 데이터 분석 및 통계 추출 중...")
    all_numbers = []
    for d in cleaned_data:
        all_numbers.extend(d["numbers"])
    
    freq_counter = Counter(all_numbers)
    frequencies = [0] * 46
    for n in range(1, 46):
        frequencies[n] = freq_counter.get(n, 0)
    
    co_matrix = {}
    for d in cleaned_data:
        nums = sorted(d["numbers"])
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair = tuple(sorted((nums[i], nums[j])))
                co_matrix[pair] = co_matrix.get(pair, 0) + 1
    
    sorted_co = sorted(co_matrix.items(), key=lambda x: x[1], reverse=True)
    top_20 = sorted_co[:20]
    formatted_co = [{"a": a, "b": b, "w": w} for (a, b), w in top_20]
    
    # 최근 5회차 데이터 추출 (최신순)
    recent_5 = cleaned_data[-5:][::-1]
    
    # 3. HTML 파일 업데이트
    print(f"3. 웹서비스 소스 코드 업데이트 중: {HTML_PATH}")
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 빈도수 데이터 교체
    html_content = re.sub(
        r"frequencies: \[0,.*?\],",
        f"frequencies: {json.dumps(frequencies)},",
        html_content
    )
    
    # 공출현 가중치 데이터 교체
    html_content = re.sub(
        r"coWeights: \[.*?\]",
        f"coWeights: {json.dumps(formatted_co)}",
        html_content,
        flags=re.DOTALL
    )

    # 최근 5회 당첨 데이터 교체
    html_content = re.sub(
        r"const RECENT_HISTORY_DATA = \[.*?\];",
        f"const RECENT_HISTORY_DATA = {json.dumps(recent_5)};",
        html_content,
        flags=re.DOTALL
    )
    
    # 버전 정보 및 문구 교체 (제작자 정보 및 배지 포함)
    html_content = re.sub(r"\(v\d+\)", f"(v{latest_draw})", html_content)
    html_content = re.sub(r">v\d+</span>", f">v{latest_draw}</span>", html_content)
    html_content = re.sub(r"\d+회차 전수 조사를 통한", f"{latest_draw}회차 전수 조사를 통한", html_content)
    
    # 제작자 정보가 없을 경우를 대비해 푸터 영역 보강
    if "건뚱" not in html_content:
        footer_pattern = r'<div class="footer-info">.*?</div>'
        new_footer = f"""<div class="footer-info">
            <p>© 2026 Premium Lotto - All Rights Reserved</p>
            <p><strong>건뚱</strong> 에 의해 제작되었습니다</p>
            <p class="data-source-info">현재 회차: <span id="latest-draw-no">{latest_draw}</span>회차 데이터 분석 완료 | 데이터 출처: 동행복권 제공</p>
        </div>"""
        html_content = re.sub(footer_pattern, new_footer, html_content, flags=re.DOTALL)
    
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 4. lottoData.js 업데이트
    LOTTO_DATA_PATH = os.path.join(BASE_DIR, "js", "lottoData.js")
    if os.path.exists(LOTTO_DATA_PATH):
        print(f"4. 코어 데이터 파일 업데이트 중: {LOTTO_DATA_PATH}")
        new_lotto_data = f"""/**
 * 1회부터 {latest_draw}회차까지의 실제 로또 당첨 데이터 분석 결과 (자동 업데이트됨)
 */

export const FULL_HISTORY_FREQUENCIES = {json.dumps(frequencies)};

export const getFullCoOccurrenceMatrix = () => {{
    const matrix = Array(46).fill(0).map(() => Array(46).fill(0));
    const patterns = {json.dumps(formatted_co)};

    patterns.forEach(p => {{
        matrix[p.a][p.b] = p.w;
        matrix[p.b][p.a] = p.w;
    }});

    return matrix;
}};
"""
        with open(LOTTO_DATA_PATH, "w", encoding="utf-8") as f:
            f.write(new_lotto_data)

    print(f"--- 업데이트 완료! 현재 서비스 버전: v{latest_draw} ---")

if __name__ == "__main__":
    update_service()
