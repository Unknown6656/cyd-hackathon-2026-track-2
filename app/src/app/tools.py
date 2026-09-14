# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
#
# Tools should be thin wrappers around existing application functions.
# They translate agent-friendly inputs into calls to your domain layer.
# ---------------------------------------------------------------------------


def calculate_result(value: float, multiplier: float) -> float:
    """Existing application function."""
    return value * multiplier


def calculate_percentage_change(old: float, new: float) -> float:
    """Existing application function."""
    if old == 0:
        raise ValueError("Cannot calculate percentage change from zero.")

    return ((new - old) / old) * 100


def calculate_average(values: list[float]) -> float:
    """Existing application function."""
    if not values:
        raise ValueError("At least one value is required.")

    return sum(values) / len(values)
