import {
    FULL_HISTORY_FREQUENCIES,
    RECENT_30_FREQUENCIES,
    RECENT_10_FREQUENCIES,
    MISSING_DRAWS,
    LAST_DRAW_NUMBERS,
    getFullCoOccurrenceMatrix
} from './lottoData.js';

export class LottoRecommender {
    constructor() {
        this.freqs = [...FULL_HISTORY_FREQUENCIES];
        this.recent30 = [...RECENT_30_FREQUENCIES];
        this.recent10 = [...RECENT_10_FREQUENCIES];
        this.missing = [...MISSING_DRAWS];
        this.lastDraw = [...LAST_DRAW_NUMBERS];
        this.coMatrix = getFullCoOccurrenceMatrix();
    }

    /**
     * ① 장기 빈도 + 단기 트렌드(30회/10회) + 미출현 회귀 주기 + 직전회차 이월수/이웃수(±1) 복합 초기 가중치 계산
     */
    createInitialProbabilities(excludedSet = new Set()) {
        const probs = Array(46).fill(0);
        const avgFreq = this.freqs.slice(1).reduce((a, b) => a + b, 0) / 45 || 162;

        const lastSet = new Set(this.lastDraw);
        const neighborSet = new Set();
        this.lastDraw.forEach(n => {
            if (n > 1 && !lastSet.has(n - 1)) neighborSet.add(n - 1);
            if (n < 45 && !lastSet.has(n + 1)) neighborSet.add(n + 1);
        });

        for (let i = 1; i <= 45; i++) {
            if (excludedSet.has(i)) {
                probs[i] = 0;
                continue;
            }

            // 1) 역대 누적 빈도 베이스 (비중 완만화: 약 25점 기준)
            const longTermScore = 25 * (this.freqs[i] / avgFreq);

            // 2) 최근 30회 & 10회 단기 트렌드 가중치 (핫 넘버 반영)
            const trendScore = (this.recent30[i] * 5.5) + (this.recent10[i] * 8.0);

            // 3) 장기 미출현(콜드 넘버) 회귀 주기 보정
            let coldScore = 0;
            const miss = this.missing[i];
            if (miss >= 15) {
                coldScore = 18 + Math.min(miss - 15, 10) * 1.5;
            } else if (miss >= 10) {
                coldScore = 10 + (miss - 10) * 1.5;
            }

            // 4) 직전 회차 이월수 및 이웃수(±1) 가중치
            let carryNeighborScore = 0;
            if (lastSet.has(i)) {
                carryNeighborScore = 18;
            } else if (neighborSet.has(i)) {
                carryNeighborScore = 14;
            }

            probs[i] = longTermScore + trendScore + coldScore + carryNeighborScore;
        }

        return probs;
    }

    /**
     * ② 45x45 전체 번호 쌍 동반 출현(상관관계) 정규화 가중치 및 인접/연번 군집 시너지 업데이트
     */
    updateWeights(picked, probabilities, selected, excludedSet = new Set()) {
        const row = this.coMatrix[picked];
        if (!row) return;

        let sumCo = 0;
        let minCo = Infinity;
        let count = 0;
        for (let j = 1; j <= 45; j++) {
            if (j === picked) continue;
            const w = row[j] || 0;
            sumCo += w;
            if (w < minCo) minCo = w;
            count++;
        }
        const avgCo = count > 0 ? sumCo / count : 20;
        if (!isFinite(minCo)) minCo = 0;

        for (let j = 1; j <= 45; j++) {
            if (!selected.includes(j) && !excludedSet.has(j)) {
                const coCount = row[j] || 0;
                // 전체 45x45 동반출현 상대 편차 반영 (특정 상위 20개 쌍 쏠림 방지)
                const baseCoBoost = Math.max(0, coCount - minCo) * 1.6;
                const aboveAvgBoost = Math.max(0, coCount - avgCo) * 3.2;

                // 자연스러운 연속 번호(±1) 및 인접 구간(±2) 군집 시너지
                const dist = Math.abs(picked - j);
                let clusterBoost = 0;
                if (dist === 1) {
                    clusterBoost = 12 + Math.max(0, coCount - avgCo) * 1.5;
                } else if (dist === 2) {
                    clusterBoost = 6;
                }

                probabilities[j] += baseCoBoost + aboveAvgBoost + clusterBoost;
            }
        }
    }

    drawFromECDF(probabilities, selected = [], excludedSet = new Set()) {
        const currentProbs = [...probabilities];
        selected.forEach(n => currentProbs[n] = 0);
        excludedSet.forEach(n => currentProbs[n] = 0);

        const totalWeight = currentProbs.reduce((a, b) => a + b, 0);
        if (totalWeight <= 0) {
            const available = [];
            for (let i = 1; i <= 45; i++) {
                if (!selected.includes(i) && !excludedSet.has(i)) available.push(i);
            }
            return available[Math.floor(Math.random() * available.length)] || 1;
        }

        const r = Math.random() * totalWeight;
        let s = 0;
        for (let i = 1; i <= 45; i++) {
            s += currentProbs[i];
            if (r <= s && currentProbs[i] > 0) return i;
        }
        return 45;
    }

    /**
     * 인위적 밸런스 필터(③) 없이 ① + ② 확률 모델만으로 자연스럽게 6개 번호 추출
     */
    generateNumbers(fixedNumbers = [], excludedNumbers = []) {
        const selected = [...fixedNumbers].slice(0, 5);
        const excludedSet = new Set(excludedNumbers);
        const currentProbabilities = this.createInitialProbabilities(excludedSet);

        selected.forEach(fixedNum => {
            this.updateWeights(fixedNum, currentProbabilities, selected, excludedSet);
        });

        while (selected.length < 6) {
            const picked = this.drawFromECDF(currentProbabilities, selected, excludedSet);
            selected.push(picked);
            this.updateWeights(picked, currentProbabilities, selected, excludedSet);
        }

        return selected.sort((a, b) => a - b);
    }

    generateGames(gameCount = 5, fixedNumbers = [], excludedNumbers = []) {
        const games = [];
        for (let i = 0; i < gameCount; i++) {
            games.push(this.generateNumbers(fixedNumbers, excludedNumbers));
        }
        return games;
    }
}
