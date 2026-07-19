"""
ai_predictor.py
----------------
A simple, explainable rule-based "AI" prediction engine.
It takes sensor readings (temperature, vibration, pressure, rpm) and
outputs a health score, status, failure probability, confidence,
estimated Remaining Useful Life (RUL), and a suggested action.

This mimics how a real ML model's output would be consumed, so it can
later be swapped for a trained model (e.g. scikit-learn) without
changing the rest of the app.
"""

# Ideal / safe operating ranges for a generic industrial machine.
# In a real system these would differ per machine type.
SAFE_RANGES = {
    "temperature": (40, 85),   # Celsius
    "vibration": (0, 4.5),     # mm/s
    "pressure": (20, 100),     # PSI
    "rpm": (500, 3000),        # revolutions per minute
}


def _deviation_score(value, low, high):
    """
    Returns a 0-100 'health contribution' score for a single sensor value.
    100 = perfectly within the safe range.
    Score drops the further the value strays outside the range.
    """
    if low <= value <= high:
        return 100.0

    # How far outside the range, as a percentage of the range width
    range_width = high - low
    if value < low:
        deviation = (low - value) / range_width
    else:
        deviation = (value - high) / range_width

    # Cap deviation impact so score never goes below 0
    penalty = min(deviation * 100, 100)
    return max(100 - penalty, 0)


def predict_health(temperature, vibration, pressure, rpm):
    """
    Main prediction function.
    Returns a dictionary with all AI output fields.
    """

    # 1. Score each sensor individually
    temp_score = _deviation_score(temperature, *SAFE_RANGES["temperature"])
    vib_score = _deviation_score(vibration, *SAFE_RANGES["vibration"])
    pressure_score = _deviation_score(pressure, *SAFE_RANGES["pressure"])
    rpm_score = _deviation_score(rpm, *SAFE_RANGES["rpm"])

    # 2. Weighted overall health score.
    #    Vibration and temperature are typically the strongest early
    #    indicators of mechanical failure, so they're weighted higher.
    health_score = round(
        (temp_score * 0.30) +
        (vib_score * 0.35) +
        (pressure_score * 0.20) +
        (rpm_score * 0.15),
        1
    )

    # 3. Classify status based on health score
    if health_score >= 80:
        status = "Healthy"
    elif health_score >= 50:
        status = "Warning"
    else:
        status = "Critical"

    # 4. Failure probability is the inverse of health score (simple mapping)
    failure_probability = round(100 - health_score, 1)

    # 5. Confidence: higher when sensor values aren't borderline
    #    (a simple heuristic - not borderline near range edges = more confident)
    scores = [temp_score, vib_score, pressure_score, rpm_score]
    spread = max(scores) - min(scores)
    confidence = round(max(70, 100 - spread / 2), 1)

    # 6. Estimated Remaining Useful Life (RUL) in days.
    #    Simple linear mapping: 100 health -> ~90 days, 0 health -> 0 days.
    rul_days = int(round((health_score / 100) * 90))

    # 7. Suggested action based on status
    if status == "Healthy":
        suggested_action = "No action needed. Continue routine monitoring."
    elif status == "Warning":
        suggested_action = "Schedule inspection within the next 7-10 days."
    else:
        suggested_action = "Immediate maintenance required. Stop machine if possible."

    return {
        "health_score": health_score,
        "status": status,
        "failure_probability": failure_probability,
        "confidence": confidence,
        "rul_days": rul_days,
        "suggested_action": suggested_action,
        "sensor_breakdown": {
            "temperature_score": round(temp_score, 1),
            "vibration_score": round(vib_score, 1),
            "pressure_score": round(pressure_score, 1),
            "rpm_score": round(rpm_score, 1),
        }
    }