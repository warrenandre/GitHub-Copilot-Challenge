window.snakeCashRushBridge = {
  raf(callback) {
    return window.requestAnimationFrame(callback);
  },

  cancelRaf(handle) {
    window.cancelAnimationFrame(handle);
  },

  readBestScore() {
    return Number.parseInt(window.localStorage.getItem("snake-cash-rush-best") ?? "0", 10) || 0;
  },

  writeBestScore(score) {
    window.localStorage.setItem("snake-cash-rush-best", String(score));
  },
};