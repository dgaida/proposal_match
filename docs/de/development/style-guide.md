# Docstring Style Guide

Dieses Projekt folgt dem **Google Python Style Guide** für Docstrings. Dies gewährleistet eine konsistente, lesbare und automatisch dokumentierbare Codebasis.

## Standard-Format

Jede öffentliche Funktion, Methode, Klasse und jedes Modul muss einen Docstring enthalten.

```python
def function_name(param1: int, param2: str) -> bool:
    """
    Eine kurze Zusammenfassung der Funktion in einer Zeile.

    Eine detailliertere Beschreibung der Funktion, falls erforderlich.
    Hier können Logik, Annahmen oder Anwendungsfälle erläutert werden.

    Args:
        param1 (int): Beschreibung des ersten Parameters.
        param2 (str): Beschreibung des zweiten Parameters.

    Returns:
        bool: Beschreibung des Rückgabewerts.

    Raises:
        ValueError: Wenn param1 ungültig ist.
    """
    return True
```

## Refactoring-Beispiele

### Vorher (Nicht konform)
```python
def get_data(id):
    # Holt Daten aus der DB
    return db.query(id)
```

### Nachher (Google-Style)
```python
def get_data(record_id: int) -> dict:
    """
    Ruft einen Datensatz basierend auf der ID aus der Datenbank ab.

    Args:
        record_id (int): Die eindeutige Kennung des Datensatzes.

    Returns:
        dict: Die Daten des gefundenen Datensatzes.

    Raises:
        RecordNotFoundError: Wenn keine Daten für die ID existieren.
    """
    return db.query(record_id)
```

## Überprüfung

Die Einhaltung des Stils wird automatisch durch `interrogate` in der CI/CD-Pipeline überprüft. Eine Abdeckung von **95%** ist erforderlich.
