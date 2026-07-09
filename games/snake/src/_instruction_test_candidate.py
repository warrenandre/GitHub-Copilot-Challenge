from __future__ import annotations

# Candidate snippet generated for instruction-compliance testing.
# Not part of production gameplay code.

def compute_next_tick_speed(score: int, bills_per_speedup: int = 5) -> int:
    """
    Compute tick speed (ms) from score, capping between MIN_TICK_MS and BASE_TICK_MS.
    Speed increases by SPEED_STEP_MS for every bills_per_speedup bills collected.
    """
    if score < 0 or bills_per_speedup <= 0:
        return BASE_TICK_MS

    bills_collected = score // SCORE_PER_BILL
    speedup_count = bills_collected // bills_per_speedup
    tick_ms = BASE_TICK_MS - (speedup_count * SPEED_STEP_MS)

    return max(MIN_TICK_MS, min(BASE_TICK_MS, tick_ms))
