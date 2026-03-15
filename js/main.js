import { LottoRecommender } from './recommender.js';

document.addEventListener('DOMContentLoaded', () => {
    const recommender = new LottoRecommender();
    const generateBtn = document.getElementById('generate-btn');
    const numberDisplay = document.getElementById('number-display');
    const statusText = document.getElementById('data-status');

    let isGenerating = false;

    const createBall = (number) => {
        const ball = document.createElement('div');
        ball.className = 'lotto-ball';
        
        let colorClass = '';
        if (number <= 10) colorClass = 'ball-1-10';
        else if (number <= 20) colorClass = 'ball-11-20';
        else if (number <= 30) colorClass = 'ball-21-30';
        else if (number <= 40) colorClass = 'ball-31-40';
        else colorClass = 'ball-41-45';
        
        ball.classList.add(colorClass);
        ball.textContent = number;
        return ball;
    };

    const generate = async () => {
        if (isGenerating) return;
        isGenerating = true;
        
        // UI 초기화
        numberDisplay.innerHTML = '';
        generateBtn.disabled = true;
        generateBtn.textContent = '분석 중...';
        statusText.textContent = '패턴 분석 엔진 가동 중';

        // 분석 애니메이션 느낌을 위한 지연
        await new Promise(resolve => setTimeout(resolve, 800));

        const numbers = recommender.generateNumbers();
        
        generateBtn.textContent = '번호 생성 완료';
        statusText.textContent = '최적의 확률 조합 산출 완료';

        // 공 하나씩 등장
        for (let i = 0; i < numbers.length; i++) {
            const ball = createBall(numbers[i]);
            numberDisplay.appendChild(ball);
            await new Promise(resolve => setTimeout(resolve, 200));
        }

        setTimeout(() => {
            generateBtn.disabled = false;
            generateBtn.textContent = '다시 생성하기';
            isGenerating = false;
        }, 500);
    };

    generateBtn.addEventListener('click', generate);
});
