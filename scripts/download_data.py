import urllib.request
import json
import os

url = "https://smok95.github.io/lotto/results/all.json"
target_path = r"c:\Users\tgkw2\OneDrive\바탕 화면\project\lotto\data\lotto_history.json"

try:
    print(f"Downloading data from {url}...")
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
    
    # 정제: 필요한 필드(draw_no, numbers)만 추출하여 파일 크기 최적화
    cleaned_data = []
    for entry in data:
        cleaned_data.append({
            "draw_no": entry["draw_no"],
            "numbers": entry["numbers"]
        })
    
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully saved {len(cleaned_data)} draws to {target_path}")

except Exception as e:
    print(f"Error: {e}")
