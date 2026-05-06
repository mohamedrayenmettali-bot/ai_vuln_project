from __future__ import annotations

from datetime import datetime

from ai.utils.ml_utils import compute_age_days


def test_compute_age_days_uses_reference_date():
    age = compute_age_days("2024-01-10", datetime(2024, 1, 20))
    assert age == 10


def test_compute_age_days_caps_invalid_values_to_default():
    assert compute_age_days("not-a-date") == 365
