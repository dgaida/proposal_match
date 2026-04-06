# Docstring Style Guide

This project follows the **Google Python Style Guide** for docstrings. This ensures a consistent, readable, and automatically documentable codebase.

## Standard Format

Every public function, method, class, and module must include a docstring.

```python
def function_name(param1: int, param2: str) -> bool:
    """
    A short summary of the function in one line.

    A more detailed description of the function if necessary.
    Explain logic, assumptions, or use cases here.

    Args:
        param1 (int): Description of the first parameter.
        param2 (str): Description of the second parameter.

    Returns:
        bool: Description of the return value.

    Raises:
        ValueError: If param1 is invalid.
    """
    return True
```

## Refactoring Examples

### Before (Non-compliant)
```python
def get_data(id):
    # Fetches data from DB
    return db.query(id)
```

### After (Google-style)
```python
def get_data(record_id: int) -> dict:
    """
    Retrieves a record from the database based on the ID.

    Args:
        record_id (int): The unique identifier for the record.

    Returns:
        dict: The data of the found record.

    Raises:
        RecordNotFoundError: If no data exists for the ID.
    """
    return db.query(record_id)
```

## Verification

Style compliance is automatically checked by `interrogate` in the CI/CD pipeline. A coverage of **95%** is required.
