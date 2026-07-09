// Retrieves high score from localStorage with fallback to 0 if not found or on error
function loadHighScore() {
  try {
    const score = localStorage.getItem('snakeCashRushHighScore');
    return score ? parseInt(score, 10) : 0;
  } catch (error) {
    console.error('Failed to load high score from localStorage:', error);
    return 0;
  }
}

// Saves score to localStorage; handles storage errors gracefully without breaking gameplay
function saveHighScore(score) {
  try {
    localStorage.setItem('snakeCashRushHighScore', String(score));
  } catch (error) {
    console.error('Failed to save high score to localStorage:', error);
  }
}

// Export for use in script tags
window.loadHighScore = loadHighScore;
window.saveHighScore = saveHighScore;
