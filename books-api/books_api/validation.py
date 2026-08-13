"""Body validation, written to match the schemas in openapi.yaml.

The rules here are the ones the spec advertises: which fields are required, the
length limits, the year range and the types. Keeping them in one place is what
makes it practical to check the implementation against the document.
"""
from __future__ import annotations

TITLE_MAX = 200
AUTHOR_MAX = 120
YEAR_MIN, YEAR_MAX = 1450, 2100

WRITABLE = ("title", "author", "year", "available")


class ValidationError(ValueError):
    """Raised for anything the spec describes as a 400."""


def _text(value, field: str, limit: int) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be a string.")
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValidationError(f"'{field}' cannot be empty.")
    if len(cleaned) > limit:
        raise ValidationError(
            f"'{field}' cannot be longer than {limit} characters.")
    return cleaned


def _year(value):
    if value is None:
        return None
    # bool is a subclass of int, so it has to be excluded explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("'year' must be an integer.")
    if not YEAR_MIN <= value <= YEAR_MAX:
        raise ValidationError(
            f"'year' must be between {YEAR_MIN} and {YEAR_MAX}.")
    return value


def _available(value) -> bool:
    if not isinstance(value, bool):
        raise ValidationError("'available' must be true or false.")
    return value


def _reject_unknown(body: dict) -> None:
    unknown = sorted(set(body) - set(WRITABLE))
    if unknown:
        raise ValidationError(
            "unexpected field" + ("s " if len(unknown) > 1 else " ")
            + ", ".join(f"'{f}'" for f in unknown) + ".")


def clean_new_book(body) -> dict:
    """Validate a POST body against the NewBook schema."""
    if not isinstance(body, dict):
        raise ValidationError("the body must be a JSON object.")
    if "id" in body:
        raise ValidationError("'id' is assigned by the server.")
    _reject_unknown(body)

    for field in ("title", "author"):
        if field not in body:
            raise ValidationError(f"'{field}' is required.")

    return {
        "title": _text(body["title"], "title", TITLE_MAX),
        "author": _text(body["author"], "author", AUTHOR_MAX),
        "year": _year(body.get("year")),
        "available": _available(body.get("available", True)),
    }


def clean_update(body) -> dict:
    """Validate a PUT body against the BookUpdate schema.

    Only the fields present are returned, so the caller can update one field
    without resending the others.
    """
    if not isinstance(body, dict):
        raise ValidationError("the body must be a JSON object.")
    if "id" in body:
        raise ValidationError("'id' cannot be changed.")
    _reject_unknown(body)
    if not body:
        raise ValidationError("the body must contain at least one field.")

    changes = {}
    if "title" in body:
        changes["title"] = _text(body["title"], "title", TITLE_MAX)
    if "author" in body:
        changes["author"] = _text(body["author"], "author", AUTHOR_MAX)
    if "year" in body:
        changes["year"] = _year(body["year"])
    if "available" in body:
        changes["available"] = _available(body["available"])
    return changes
