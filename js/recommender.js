import { FULL_HISTORY_FREQUENCIES, getFullCoOccurrenceMatrix } from './lottoData.js';

export class LottoRecommender {
    constructor() {
        // 1회~1215회 전체 이력 빈도 반영
        this.baseFrequencies = [...FULL_HISTORY_FREQUENCIES];
        this.coOccurrenceMatrix = getFullCoOccurrenceMatrix();
    }

    /**
     * Empirical CDF를 활용한 가중치 기반 무작위 추출
     */
    drawFromECDF(probabilities) {
        let totalWeight = 0;
        for (let i = 1; i <= 45; i++) {
            totalWeight += probabilities[i];
        }

        if (totalWeight === 0) return Math.floor(Math.random() * 45) + 1;

        const cumulativeProbs = [];
        let runningSum = 0;
        for (let i = 1; i <= 45; i++) {
            runningSum += probabilities[i];
            cumulativeProbs.push({ number: i, cumulative: runningSum });
        }

        const randomValue = Math.random() * totalWeight;
        for (const item of cumulativeProbs) {
            if (randomValue <= item.cumulative) {
                return item.number;
            }
        }
        return 45;
    }

    /**
     * 전체 이력 및 실시간 공출현 패턴을 반영한 번호 생성
     */
    generateNumbers() {
        const selected = [];
        // 초기 확률: 전체 이력 빈도
        let currentProbabilities = [...this.baseFrequencies];

        for (let i = 0; i < 6; i++) {
            // 이미 선택된 숫자 제외
            selected.forEach(num => {
                currentProbabilities[num] = 0;
            });

            const picked = this.drawFromECDF(currentProbabilities);
            selected.push(picked);

            // 공출현 패턴 분석: 방금 뽑힌 숫자와 과거에 함께 자주 등장했던 숫자들의 확률 대폭 상향
            const coOccurrenceWeights = this.coOccurrenceMatrix[picked];
            for (let j = 1; j <= 45; j++) {
                if (!selected.includes(j)) {
                    // 전체 이력 기반 상관관계 가중치 적용 (가중치 계수 조절 가능)
                    currentProbabilities[j] += coOccurrenceWeights[j] * 10; 
                }
            }
        }

        return selected.sort((a, b) => a - b);
    }
}
