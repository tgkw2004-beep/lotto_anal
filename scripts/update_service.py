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


def analyze_lotto_data(cleaned_data):
    total_draws = len(cleaned_data)

    # 1. 전체 누적 출현 빈도 (1~45)
    all_numbers = []
    for d in cleaned_data:
        all_numbers.extend(d["numbers"])
    freq_counter = Counter(all_numbers)
    frequencies = [0] + [freq_counter.get(n, 0) for n in range(1, 46)]

    # 2. 최근 30회차 및 최근 10회차 단기 출현 빈도 (핫 넘버 트렌드)
    recent_30_draws = cleaned_data[-30:] if total_draws >= 30 else cleaned_data
    recent_10_draws = cleaned_data[-10:] if total_draws >= 10 else cleaned_data

    r30_counter = Counter(n for d in recent_30_draws for n in d["numbers"])
    r10_counter = Counter(n for d in recent_10_draws for n in d["numbers"])

    recent30_freqs = [0] + [r30_counter.get(n, 0) for n in range(1, 46)]
    recent10_freqs = [0] + [r10_counter.get(n, 0) for n in range(1, 46)]

    # 3. 미출현 주기 (마지막 출현 이후 경과 회차 수, 직전 회차 출현 시 0)
    missing_draws = [total_draws] * 46
    missing_draws[0] = 0
    for idx, d in enumerate(cleaned_data):
        from_end = total_draws - 1 - idx
        for n in d["numbers"]:
            if from_end < missing_draws[n]:
                missing_draws[n] = from_end

    # 4. 45x45 전체 번호 쌍 동반 출현(Co-occurrence) 매트릭스
    co_matrix_2d = [[0] * 46 for _ in range(46)]
    co_pairs = {}
    for d in cleaned_data:
        nums = sorted(d["numbers"])
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                a, b = nums[i], nums[j]
                co_matrix_2d[a][b] += 1
                co_matrix_2d[b][a] += 1
                co_pairs[(a, b)] = co_pairs.get((a, b), 0) + 1

    sorted_co = sorted(co_pairs.items(), key=lambda x: x[1], reverse=True)
    top_20 = [{"a": a, "b": b, "w": w} for (a, b), w in sorted_co[:20]]

    return {
        "frequencies": frequencies,
        "recent30Freqs": recent30_freqs,
        "recent10Freqs": recent10_freqs,
        "missingDraws": missing_draws,
        "coMatrix": co_matrix_2d,
        "coWeights": top_20,
    }


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
    print("2. 전수 데이터 분석 및 트렌드/미출현/전체 동반출현 통계 추출 중...")
    stats = analyze_lotto_data(cleaned_data)

    # 최근 5회차 데이터 추출 (최신순)
    recent_5 = cleaned_data[-5:][::-1]

    # 3. HTML 파일 업데이트
    print(f"3. 웹서비스 소스 코드 업데이트 중: {HTML_PATH}")
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 빈도수 및 신규 트렌드 데이터 교체
    html_content = re.sub(
        r"frequencies: \[0,.*?\],",
        f"frequencies: {json.dumps(stats['frequencies'])},",
        html_content,
    )
    html_content = re.sub(
        r"recent30Freqs: \[0,.*?\],",
        f"recent30Freqs: {json.dumps(stats['recent30Freqs'])},",
        html_content,
    )
    html_content = re.sub(
        r"recent10Freqs: \[0,.*?\],",
        f"recent10Freqs: {json.dumps(stats['recent10Freqs'])},",
        html_content,
    )
    html_content = re.sub(
        r"missingDraws: \[0,.*?\],",
        f"missingDraws: {json.dumps(stats['missingDraws'])},",
        html_content,
    )
    html_content = re.sub(
        r"coMatrix: \[\[0,.*?\]\],",
        f"coMatrix: {json.dumps(stats['coMatrix'], separators=(',', ':'))},",
        html_content,
        flags=re.DOTALL,
    )
    html_content = re.sub(
        r"coWeights: \[.*?\]",
        f"coWeights: {json.dumps(stats['coWeights'])}",
        html_content,
        flags=re.DOTALL,
    )

    # 최근 5회 당첨 데이터 교체
    html_content = re.sub(
        r"const RECENT_HISTORY_DATA = \[.*?\];",
        f"const RECENT_HISTORY_DATA = {json.dumps(recent_5)};",
        html_content,
        flags=re.DOTALL,
    )

    # 버전 정보 및 문구 교체 (제작자 정보 및 배지 포함)
    html_content = re.sub(r"\(v\d+\)", f"(v{latest_draw})", html_content)
    html_content = re.sub(r">v\d+</span>", f">v{latest_draw}</span>", html_content)
    html_content = re.sub(r"\d+회차 전수 조사를 통한", f"{latest_draw}회차 전수 조사를 통한", html_content)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 4. lottoData.js 업데이트
    lotto_data_path = os.path.join(BASE_DIR, "js", "lottoData.js")
    if os.path.exists(lotto_data_path):
        print(f"4. 코어 데이터 파일 업데이트 중: {lotto_data_path}")
        new_lotto_data = f"""/**
 * 1회부터 {latest_draw}회차까지의 실제 로또 당첨 데이터 분석 결과 (자동 업데이트됨)
 */

export const FULL_HISTORY_FREQUENCIES = {json.dumps(stats['frequencies'])};
export const RECENT_30_FREQUENCIES = {json.dumps(stats['recent30Freqs'])};
export const RECENT_10_FREQUENCIES = {json.dumps(stats['recent10Freqs'])};
export const MISSING_DRAWS = {json.dumps(stats['missingDraws'])};
export const LAST_DRAW_NUMBERS = {json.dumps(recent_5[0]['numbers'])};

export const FULL_CO_MATRIX = {json.dumps(stats['coMatrix'], separators=(',', ':'))};

export const getFullCoOccurrenceMatrix = () => {{
    return FULL_CO_MATRIX.map(row => [...row]);
}};
"""
        with open(lotto_data_path, "w", encoding="utf-8") as f:
            f.write(new_lotto_data)

    print(f"--- 업데이트 완료! 현재 서비스 버전: v{latest_draw} ---")


if __name__ == "__main__":
    update_service()
