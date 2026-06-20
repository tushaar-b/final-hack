def size_position(conviction_score: float, current_sector_exposure_pct: float) -> float:
    """
    Determines the position size percentage (0.0 to 100.0) based on conviction score
    and current sector exposure. Maps conviction 6.0 -> 2% and 10.0 -> 4%.
    """
    if conviction_score < 5.0:
        return 0.0  # HOLD, no position sizing needed
        
    # Continuous linear sizing from 1.0% (for score 5.0) to 4.0% (for score 10.0)
    base = 1.0 + ((conviction_score - 5.0) / 5.0) * 3.0
    base = round(base, 2)
        
    # Cap at 25% sector exposure
    if current_sector_exposure_pct + base > 25.0:
        return max(0.0, 25.0 - current_sector_exposure_pct)
        
    return base
