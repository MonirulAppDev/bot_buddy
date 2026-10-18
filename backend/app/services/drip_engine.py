import random
import time
from datetime import datetime, timezone


def get_stochastic_delay(base_interval_seconds: float, min_floor: float = 0.5) -> float:
    """Calculate a human-like delay using Gaussian distribution around the base interval.
    Ensures delay never drops below min_floor.
    """
    if base_interval_seconds <= 0:
        return min_floor

    # Standard deviation is roughly 25% of base interval
    std_dev = max(0.3, base_interval_seconds * 0.25)
    sampled = random.gauss(base_interval_seconds, std_dev)
    
    # Add a slight jitter
    jitter = random.uniform(-0.2, 0.4)
    final_delay = max(min_floor, sampled + jitter)
    return round(final_delay, 2)


def is_peak_hour() -> bool:
    """Determine if current time is within typical social media peak engagement hours (11:00 - 23:00)."""
    current_hour = datetime.now(timezone.utc).hour
    return 6 <= current_hour <= 18  # Approximate global daytime
