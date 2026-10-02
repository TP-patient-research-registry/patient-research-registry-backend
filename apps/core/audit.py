def mask_value(value: str) -> str:
    """Audit log mask for health data: record that a field changed, never its value."""
    return "***"
