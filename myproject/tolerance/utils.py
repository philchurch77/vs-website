from collections import Counter
from .models import Keyword


def compute_zone_summary(keywords):
    zones = [k.default_zone for k in keywords]
    c = Counter(zones)

    hyper = c.get(Keyword.Zone.HYPER, 0)
    window = c.get(Keyword.Zone.WINDOW, 0)
    hypo = c.get(Keyword.Zone.HYPO, 0)

    score = window - (hyper + hypo)

    # Decide label (tie-breaker prefers WINDOW)
    if window >= hyper and window >= hypo:
        today_label = "In window"
    elif hyper >= hypo:
        today_label = "Hyper-aroused"
    else:
        today_label = "Hypo-aroused"

    return {
        "counts": {"hyper": hyper, "window": window, "hypo": hypo},
        "score": score,
        "today_label": today_label,
    }
