from collections import Counter
from .models import Keyword


def compute_zone_summary(keywords):
    hyper = sum(1 for k in keywords if k.default_zone == "HYPER")
    window = sum(1 for k in keywords if k.default_zone == "WINDOW")
    hypo = sum(1 for k in keywords if k.default_zone == "HYPO")

    score = hyper - hypo
    if score >= 2:
        today_label = "Leaning hyper"
    elif score <= -2:
        today_label = "Leaning hypo"
    else:
        today_label = "In/near window"

    return {
        "counts": {"hyper": hyper, "window": window, "hypo": hypo},
        "score": score,
        "today_label": today_label,
    }

