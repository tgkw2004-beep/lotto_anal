import json
from collections import Counter

file_path = r"c:\Users\tgkw2\OneDrive\바탕 화면\project\lotto\data\lotto_history.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. Frequency Analysis
all_numbers = []
for entry in data:
    all_numbers.extend(entry["numbers"])

freq_counter = Counter(all_numbers)
frequencies = [0] * 46
for num in range(1, 46):
    frequencies[num] = freq_counter.get(num, 0)

print("--- Frequencies ---")
print(frequencies)

# 2. Co-occurrence Analysis
co_matrix = {}
for entry in data:
    nums = sorted(entry["numbers"])
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            pair = tuple(sorted((nums[i], nums[j])))
            co_matrix[pair] = co_matrix.get(pair, 0) + 1

# Get top 20 co-occurrences
sorted_co = sorted(co_matrix.items(), key=lambda x: x[1], reverse=True)
top_20 = sorted_co[:20]

print("\n--- Top 20 Co-occurrences ---")
formatted_co = []
for (a, b), w in top_20:
    formatted_co.append(f"{{a: {a}, b: {b}, w: {w}}}")

print("[" + ", ".join(formatted_co) + "]")
