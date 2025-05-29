// Vollständiges JavaScript für Enhanced Quiz
// Erweiterte Spielvariablen
let currentQuestionIndex = 0;
let score = 0;
let questions = [];
let randomizedQuestions = [];
let selectedCategory = '';
let timeLeft = 30;
let timerInterval = null;
let questionStartTime = null;
let answerTimes = [];
let soundEnabled = true;
let difficulty = 'normal';
let gameStats = {
    totalQuestions: 0,
    correctAnswers: 0,
    averageTime: 0,
    accuracy: 0
};

// Schwierigkeitsgrade
const difficulties = {
    normal: { time: 30, label: 'Normal' },
    hard: { time: 20, label: 'Schwer' },
    expert: { time: 15, label: 'Experte' }
};

// Sound-Effekte (Web Audio API)
let audioContext = null;

function initAudio() {
    if (!audioContext && window.AudioContext) {
        try {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.log('Audio context not supported');
            soundEnabled = false;
        }
    }
}

function playSound(frequency, duration = 200, type = 'sine') {
    if (!soundEnabled || !audioContext) return;

    try {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.value = frequency;
        oscillator.type = type;

        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration / 1000);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + duration / 1000);
    } catch (e) {
        console.log('Sound playback failed:', e);
    }
}

// Loading Overlay Funktionen
function showLoadingOverlay(show = true) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }
}

// Partikel-System
function createParticles() {
    const particles = document.getElementById('particles');
    if (!particles) return;

    particles.innerHTML = '';

    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (Math.random() * 15 + 15) + 's';
        particles.appendChild(particle);
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // Animation
    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Schwierigkeit aktualisieren
function updateDifficulty() {
    const select = document.getElementById('difficulty');
    if (select) {
        difficulty = select.value;
        console.log('Difficulty updated to:', difficulty);
    }
}

// Sound Toggle
function toggleSound() {
    soundEnabled = !soundEnabled;
    const soundIcon = document.querySelector('.sound-icon');
    if (soundIcon) {
        soundIcon.textContent = soundEnabled ? '🔊' : '🔇';
    }

    if (soundEnabled) {
        showToast('Sound aktiviert', 'success');
        playSound(523.25, 200); // Test sound
    } else {
        showToast('Sound deaktiviert', 'info');
    }
}

// Hauptspiel-Funktionen
async function startGame(category) {
    console.log('Starting game for category:', category);

    initAudio();
    showLoadingOverlay(true);

    try {
        selectedCategory = category;

        // UI Updates
        const intro = document.getElementById('intro');
        const questionScreen = document.getElementById('question-screen');
        const progressContainer = document.getElementById('progress-container');
        const timerContainer = document.getElementById('timer-container');

        if (intro) intro.classList.add('hidden');
        if (questionScreen) questionScreen.classList.remove('hidden');
        if (progressContainer) progressContainer.classList.remove('hidden');
        if (timerContainer) timerContainer.classList.remove('hidden');

        // Fragen laden
        questions = await fetchQuestions();
        if (questions.length === 0) {
            throw new Error('Keine Fragen gefunden');
        }

        randomizedQuestions = questions.sort(() => 0.5 - Math.random()).slice(0, 10);
        gameStats.totalQuestions = randomizedQuestions.length;

        currentQuestionIndex = 0;
        score = 0;
        answerTimes = [];

        showQuestion();
        playSound(523.25); // C5 - Start Sound

    } catch (error) {
        console.error('Fehler beim Starten des Spiels:', error);
        showToast('Fehler beim Laden der Fragen', 'error');

        // Fallback zu Intro zurück
        const intro = document.getElementById('intro');
        const questionScreen = document.getElementById('question-screen');
        if (intro) intro.classList.remove('hidden');
        if (questionScreen) questionScreen.classList.add('hidden');
    } finally {
        showLoadingOverlay(false);
    }
}

async function fetchQuestions() {
    try {
        const response = await fetch(`/quiz_questions/${selectedCategory}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        console.log('Fetched questions:', data);
        return data;
    } catch (error) {
        console.error('Fehler beim Laden der Fragen:', error);
        return [];
    }
}

function showQuestion() {
    const questionData = randomizedQuestions[currentQuestionIndex];
    if (!questionData) {
        console.error('No question data available');
        return;
    }

    questionStartTime = Date.now();

    // UI Updates
    updateQuestionDisplay(questionData);
    updateProgressBar();
    resetAnswerState();

    // Timer starten
    startTimer();

    // Animation
    const card = document.getElementById('question-card');
    if (card) {
        card.classList.remove('slide-up');
        setTimeout(() => card.classList.add('slide-up'), 50);
    }
}

function updateQuestionDisplay(questionData) {
    // Question Number
    const questionNumber = document.getElementById('question-number');
    if (questionNumber) {
        questionNumber.textContent = `Frage ${currentQuestionIndex + 1}`;
    }

    // Score Display
    const scoreText = document.querySelector('#score-display .score-text');
    if (scoreText) {
        scoreText.textContent = score;
    }

    // Question Text
    const questionText = document.getElementById('question-text');
    if (questionText) {
        questionText.textContent = questionData.question;
    }

    // Antworten erstellen
    const choicesDiv = document.getElementById('choices');
    if (choicesDiv) {
        choicesDiv.innerHTML = '';

        const choices = [questionData.choice1, questionData.choice2, questionData.choice3, questionData.choice4];
        const letters = ['A', 'B', 'C', 'D'];

        choices.forEach((choice, index) => {
            const button = document.createElement('button');
            button.className = 'choice-btn';
            button.innerHTML = `
                <div class="choice-letter">${letters[index]}</div>
                <div class="choice-text">${choice}</div>
                <div class="choice-glow"></div>
            `;
            button.onclick = () => selectAnswer(button, choice, questionData.correct);
            choicesDiv.appendChild(button);
        });
    }
}

function updateProgressBar() {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    if (progressBar) {
        const progress = (currentQuestionIndex / randomizedQuestions.length) * 100;
        progressBar.style.width = progress + '%';
    }

    if (progressText) {
        progressText.textContent = `Frage ${currentQuestionIndex + 1} von ${randomizedQuestions.length}`;
    }
}

function resetAnswerState() {
    // Result verstecken
    const result = document.getElementById('result');
    if (result) {
        result.classList.add('hidden');
    }

    // Next Button verstecken
    const nextBtn = document.getElementById('next-btn');
    if (nextBtn) {
        nextBtn.classList.add('hidden');
    }

    // Skip Button anzeigen
    const skipBtn = document.getElementById('skip-btn');
    if (skipBtn) {
        skipBtn.classList.remove('hidden');
    }
}

// Timer Funktionen
function startTimer() {
    const timerTime = difficulties[difficulty]?.time || 30;
    timeLeft = timerTime;
    updateTimerDisplay();

    if (timerInterval) {
        clearInterval(timerInterval);
    }

    timerInterval = setInterval(() => {
        timeLeft--;
        updateTimerDisplay();

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            timeoutAnswer();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const timerText = document.getElementById('timer-text');
    const timerCircle = document.getElementById('timer-circle');

    if (timerText) {
        timerText.textContent = timeLeft;
    }

    if (timerCircle) {
        const maxTime = difficulties[difficulty]?.time || 30;
        const progress = (timeLeft / maxTime) * 100;
        const offset = 100 - progress;
        timerCircle.style.strokeDashoffset = offset;

        // Farbe ändern bei wenig Zeit
        if (timeLeft <= 5) {
            timerCircle.style.stroke = 'var(--error-color)';
            if (timerText) timerText.style.color = 'var(--error-color)';
        } else if (timeLeft <= 10) {
            timerCircle.style.stroke = 'var(--warning-color)';
            if (timerText) timerText.style.color = 'var(--warning-color)';
        }
    }
}

function timeoutAnswer() {
    showToast('⏰ Zeit abgelaufen!', 'warning');
    playSound(220, 500); // A3 - Timeout sound

    const buttons = document.querySelectorAll('.choice-btn');
    if (buttons.length > 0) {
        // Zufällige falsche Antwort wählen
        const randomIndex = Math.floor(Math.random() * buttons.length);
        selectAnswer(buttons[randomIndex], 'TIMEOUT', randomizedQuestions[currentQuestionIndex].correct);
    }
}

// Antwort-Funktionen
function selectAnswer(button, selectedChoice, correctAnswer) {
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    // Zeit messen
    if (questionStartTime) {
        const answerTime = (Date.now() - questionStartTime) / 1000;
        answerTimes.push(answerTime);
    }

    // Alle Buttons deaktivieren
    const allButtons = document.querySelectorAll('.choice-btn');
    allButtons.forEach(btn => {
        btn.classList.add('disabled');
        btn.onclick = null;
    });

    // Skip Button verstecken
    const skipBtn = document.getElementById('skip-btn');
    if (skipBtn) {
        skipBtn.classList.add('hidden');
    }

    // Ergebnis anzeigen
    showAnswerResult(button, selectedChoice, correctAnswer, allButtons);

    // Next Button anzeigen
    const nextBtn = document.getElementById('next-btn');
    if (nextBtn) {
        nextBtn.classList.remove('hidden');
    }
}

function showAnswerResult(button, selectedChoice, correctAnswer, allButtons) {
    const resultDiv = document.getElementById('result');
    const resultIcon = document.getElementById('result-icon');
    const resultText = document.getElementById('result-text');

    if (!resultDiv || !resultIcon || !resultText) return;

    resultDiv.classList.remove('hidden');

    if (selectedChoice === correctAnswer && selectedChoice !== 'TIMEOUT') {
        // Richtig
        button.classList.add('correct');
        resultDiv.className = 'result correct';
        resultIcon.textContent = '🎉';
        resultText.textContent = 'Richtig!';
        score++;
        gameStats.correctAnswers++;

        // Score Display aktualisieren
        const scoreText = document.querySelector('#score-display .score-text');
        if (scoreText) {
            scoreText.textContent = score;
        }

        playSound(523.25, 300); // C5 - Success sound
        showToast('Richtig! +1 Punkt', 'success');

    } else {
        // Falsch oder Timeout
        if (selectedChoice !== 'TIMEOUT') {
            button.classList.add('wrong');
        }

        // Richtige Antwort markieren
        const correctButton = Array.from(allButtons).find(btn =>
            btn.querySelector('.choice-text')?.textContent === correctAnswer
        );
        if (correctButton) {
            correctButton.classList.add('correct');
        }

        resultDiv.className = 'result wrong';
        resultIcon.textContent = selectedChoice === 'TIMEOUT' ? '⏰' : '❌';

        if (selectedChoice === 'TIMEOUT') {
            resultText.textContent = `Zeit abgelaufen! Die richtige Antwort ist: ${correctAnswer}`;
        } else {
            resultText.textContent = `Falsch! Die richtige Antwort ist: ${correctAnswer}`;
        }

        playSound(220, 500); // A3 - Wrong sound
    }
}

function skipQuestion() {
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    showToast('Frage übersprungen', 'info');
    playSound(330, 200); // E4 - Skip sound

    nextQuestion();
}

function nextQuestion() {
    currentQuestionIndex++;
    if (currentQuestionIndex < randomizedQuestions.length) {
        showQuestion();
    } else {
        endGame();
    }
}

// Spiel-Ende Funktionen
async function endGame() {
    // UI umschalten
    const questionScreen = document.getElementById('question-screen');
    const progressContainer = document.getElementById('progress-container');
    const timerContainer = document.getElementById('timer-container');
    const endScreen = document.getElementById('end-screen');

    if (questionScreen) questionScreen.classList.add('hidden');
    if (progressContainer) progressContainer.classList.add('hidden');
    if (timerContainer) timerContainer.classList.add('hidden');
    if (endScreen) endScreen.classList.remove('hidden');

    // Statistiken berechnen
    calculateGameStats();

    // UI aktualisieren
    updateEndScreenDisplay();

    // Highscore prüfen
    await checkAndHandleHighscore();

    // Erfolgs-Sound
    playSound(659.25, 500); // E5 - End game sound
}

function calculateGameStats() {
    gameStats.accuracy = gameStats.totalQuestions > 0 ?
        Math.round((gameStats.correctAnswers / gameStats.totalQuestions) * 100) : 0;

    if (answerTimes.length > 0) {
        gameStats.averageTime = answerTimes.reduce((a, b) => a + b, 0) / answerTimes.length;
        gameStats.averageTime = Math.round(gameStats.averageTime * 10) / 10; // 1 Dezimalstelle
    }
}

function updateEndScreenDisplay() {
    // Final Score
    const finalScoreNumber = document.getElementById('final-score-number');
    if (finalScoreNumber) {
        finalScoreNumber.textContent = score;
    }

    // Score Details
    const correctAnswers = document.getElementById('correct-answers');
    const avgTime = document.getElementById('avg-time');
    const accuracy = document.getElementById('accuracy');

    if (correctAnswers) correctAnswers.textContent = gameStats.correctAnswers;
    if (avgTime) avgTime.textContent = gameStats.averageTime + 's';
    if (accuracy) accuracy.textContent = gameStats.accuracy + '%';

    // Performance Badge
    updatePerformanceBadge();

    // Trophy Animation
    const trophy = document.getElementById('result-trophy');
    if (trophy) {
        if (score >= 8) trophy.textContent = '🏆';
        else if (score >= 6) trophy.textContent = '🥈';
        else if (score >= 4) trophy.textContent = '🥉';
        else trophy.textContent = '🎯';
    }
}

function updatePerformanceBadge() {
    const badgeIcon = document.getElementById('badge-icon');
    const badgeText = document.getElementById('badge-text');

    if (!badgeIcon || !badgeText) return;

    if (score >= 9) {
        badgeIcon.textContent = '🌟';
        badgeText.textContent = 'Perfekt!';
    } else if (score >= 7) {
        badgeIcon.textContent = '🎉';
        badgeText.textContent = 'Sehr gut!';
    } else if (score >= 5) {
        badgeIcon.textContent = '👍';
        badgeText.textContent = 'Gut gemacht!';
    } else {
        badgeIcon.textContent = '💪';
        badgeText.textContent = 'Weiter üben!';
    }
}

// Highscore Funktionen
async function checkAndHandleHighscore() {
    try {
        const qualifies = await checkHighScore();
        if (qualifies) {
            const highscoreEntry = document.getElementById('highscore-entry');
            if (highscoreEntry) {
                highscoreEntry.classList.remove('hidden');
                const nameInput = document.getElementById('player-name');
                if (nameInput) {
                    nameInput.focus();
                }
            }
        }
        await displayTopScores();
    } catch (error) {
        console.error('Fehler beim Highscore-Check:', error);
    }
}

async function checkHighScore() {
    try {
        const response = await fetch(`/check_highscore/${selectedCategory}/${score}`);
        const data = await response.json();
        return data.qualifies;
    } catch (error) {
        console.error('Fehler beim Highscore-Check:', error);
        return false;
    }
}

async function submitHighscore() {
    const nameInput = document.getElementById('player-name');
    if (!nameInput) return;

    const playerName = nameInput.value.trim();
    if (!playerName) {
        showToast('Bitte gib einen Namen ein', 'warning');
        nameInput.focus();
        return;
    }

    try {
        const response = await fetch('/add_highscore', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                player_name: playerName,
                score: score,
                category: selectedCategory
            }),
        });

        if (response.ok) {
            showToast('Highscore eingetragen!', 'success');
            const highscoreEntry = document.getElementById('highscore-entry');
            if (highscoreEntry) {
                highscoreEntry.classList.add('hidden');
            }
            await displayTopScores();
            playSound(523.25, 300); // Success sound
        } else {
            throw new Error('Server error');
        }
    } catch (error) {
        console.error('Fehler beim Eintragen des Highscores:', error);
        showToast('Fehler beim Eintragen', 'error');
    }
}

async function displayTopScores() {
    try {
        const response = await fetch(`/high_scores/${selectedCategory}`);
        const scores = await response.json();

        const highscoreList = document.getElementById('highscore-list');
        if (!highscoreList) return;

        highscoreList.innerHTML = '';

        scores.forEach((scoreItem, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${scoreItem.player_name}</td>
                <td>${scoreItem.score}/10</td>
                <td>${scoreItem.timestamp}</td>
            `;
            highscoreList.appendChild(row);
        });

    } catch (error) {
        console.error('Fehler beim Laden der Highscores:', error);
    }
}

// Utility Funktionen
function handleNameKeypress(event) {
    if (event.key === 'Enter') {
        submitHighscore();
    }
}

function restartGame() {
    // Reset all variables
    currentQuestionIndex = 0;
    score = 0;
    answerTimes = [];
    gameStats = {
        totalQuestions: 0,
        correctAnswers: 0,
        averageTime: 0,
        accuracy: 0
    };

    // Clear timers
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    // UI Reset
    const endScreen = document.getElementById('end-screen');
    const intro = document.getElementById('intro');
    const progressContainer = document.getElementById('progress-container');

    if (endScreen) endScreen.classList.add('hidden');
    if (intro) intro.classList.remove('hidden');
    if (progressContainer) progressContainer.classList.add('hidden');

    playSound(440, 200); // A4 - Restart sound
    showToast('Bereit für eine neue Runde!', 'info');
}

function shareResult() {
    const shareText = `Ich habe ${score}/10 Punkte im ${selectedCategory} Quiz erreicht! 🎯`;

    if (navigator.share) {
        navigator.share({
            title: 'QQ Quizmaster Ergebnis',
            text: shareText,
            url: window.location.href
        });
    } else if (navigator.clipboard) {
        navigator.clipboard.writeText(shareText).then(() => {
            showToast('Ergebnis in Zwischenablage kopiert!', 'success');
        });
    } else {
        showToast('Teilen nicht unterstützt', 'warning');
    }
}

function goHome() {
    window.location.href = '/';
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('Quiz initialized');
    createParticles();

    // Keyboard Navigation
    document.addEventListener('keydown', function(e) {
        // Nur wenn Quiz-Screen aktiv ist
        const questionScreen = document.getElementById('question-screen');
        if (!questionScreen || questionScreen.classList.contains('hidden')) return;

        if (e.key >= '1' && e.key <= '4') {
            const buttons = document.querySelectorAll('.choice-btn:not(.disabled)');
            const index = parseInt(e.key) - 1;
            if (buttons[index]) {
                buttons[index].click();
            }
        } else if (e.key === 'Enter') {
            const nextBtn = document.getElementById('next-btn');
            if (nextBtn && !nextBtn.classList.contains('hidden')) {
                nextBtn.click();
            }
        } else if (e.key === ' ' || e.key === 'Spacebar') {
            e.preventDefault();
            const skipBtn = document.getElementById('skip-btn');
            if (skipBtn && !skipBtn.classList.contains('hidden')) {
                skipBtn.click();
            }
        }
    });

    // Auto-focus auf Name Input
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const target = mutation.target;
                if (target.id === 'highscore-entry' && !target.classList.contains('hidden')) {
                    const nameInput = target.querySelector('#player-name');
                    if (nameInput) {
                        setTimeout(() => nameInput.focus(), 100);
                    }
                }
            }
        });
    });

    const highscoreEntry = document.getElementById('highscore-entry');
    if (highscoreEntry) {
        observer.observe(highscoreEntry, { attributes: true });
    }
});

// Service Worker für bessere Performance (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(function(registration) {
                console.log('Service Worker registered:', registration.scope);
            }, function(error) {
                console.log('Service Worker registration failed:', error);
            });
    });
}