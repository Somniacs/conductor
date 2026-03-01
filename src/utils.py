def transform(data: dict) -> dict:
    """Apply transformations to input data."""
    return {k: v.upper() if isinstance(v, str) else v for k, v in data.items()}
