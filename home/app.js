let currentChallenge = 0; // 0 = pit stop

function advanceChallenge(target) {
    const cards = document.querySelectorAll('.challenge-card');
    const checkpoints = document.querySelectorAll('.checkpoint');
    const car = document.getElementById('raceCar');
    const progressFill = document.getElementById('progressFill');
    const currentDisplay = document.getElementById('currentChallenge');

    // Hide all cards, show target
    cards.forEach(card => card.classList.remove('active'));
    if (target === 0) {
        document.getElementById('challengePitStop').classList.add('active');
    } else {
        document.getElementById(`challenge${target}`).classList.add('active');
    }

    // Update checkpoints
    checkpoints.forEach((cp, i) => {
        cp.classList.remove('active');
        if (target === 0) {
            cp.classList.remove('completed');
        } else if (i + 1 < target) {
            cp.classList.add('completed');
        } else if (i + 1 === target) {
            cp.classList.add('active');
            cp.classList.remove('completed');
        } else {
            cp.classList.remove('completed');
        }
    });

    // Move car (positions: pit=0%, 1=22%, 2=46%, 3=70%, 4=70%)
    const positions = [0, 22, 46, 70];
    car.style.left = (target === 0 ? 0 : positions[target - 1]) + '%';

    // Update progress bar
    progressFill.style.width = (target / 4) * 100 + '%';
    currentDisplay.textContent = target === 0 ? 'Pit Stop' : target;

    currentChallenge = target;
}

function finishRace() {
    const car = document.getElementById('raceCar');
    const progressFill = document.getElementById('progressFill');
    const checkpoints = document.querySelectorAll('.checkpoint');

    // Complete all checkpoints
    checkpoints.forEach(cp => {
        cp.classList.add('completed');
        cp.classList.remove('active');
    });

    // Move car to finish
    car.style.left = '92%';
    progressFill.style.width = '100%';

    // Show victory modal
    setTimeout(() => {
        document.getElementById('victoryModal').classList.add('show');
    }, 800);
}

function restartRace() {
    document.getElementById('victoryModal').classList.remove('show');
    advanceChallenge(0);
}

function copyPrompt(element) {
    const code = element.querySelector('code');
    const text = code.textContent;

    navigator.clipboard.writeText(text).then(() => {
        element.classList.add('copied');
        const hint = element.querySelector('.copy-hint');
        hint.textContent = '✅ Copied!';

        setTimeout(() => {
            element.classList.remove('copied');
            hint.textContent = '📋 Click to copy';
        }, 2000);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    advanceChallenge(0);
});
