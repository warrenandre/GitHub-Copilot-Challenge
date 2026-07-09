const HIGH_SCORE_STORAGE_KEY = "snake-cash-rush-best";

// Normalize persisted scores to a safe non-negative integer.
function parseStoredScore(rawValue) {
  const parsed = Number.parseInt(rawValue ?? "0", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

// Retrieves high score from localStorage with fallback to 0 if not found or on error
function loadHighScore() {
  try {
    const score = localStorage.getItem(HIGH_SCORE_STORAGE_KEY);
    return parseStoredScore(score);
  } catch (error) {
    console.error('Failed to load high score from localStorage:', error);
    return 0;
  }
}

// Saves score to localStorage; handles storage errors gracefully without breaking gameplay
function saveHighScore(score) {
  try {
    localStorage.setItem(HIGH_SCORE_STORAGE_KEY, String(parseStoredScore(score)));
  } catch (error) {
    console.error('Failed to save high score to localStorage:', error);
  }
}

// Export for use in script tags
window.loadHighScore = loadHighScore;
window.saveHighScore = saveHighScore;
