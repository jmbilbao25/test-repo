"""Fixtures, and the glue that checks responses against openapi.yaml."""
from __future__ import annotations

import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from books_api.app import create_app

SPEC_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "openapi.yaml")


@pytest.fixture()
def client():
    app = create_app(seed=True)
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture()
def empty_client():
    app = create_app(seed=False)
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture(scope="session")
def spec() -> dict:
    with open(SPEC_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _resolve(node, root):
    """Inline every $ref, and translate OpenAPI's nullable into JSON Schema.

    jsonschema does not know what `nullable: true` means, so a field documented
    as nullable would otherwise fail validation when it comes back as null.
    """
    if isinstance(node, dict):
        if "$ref" in node:
            target = root
            for part in node["$ref"].lstrip("#/").split("/"):
                target = target[part]
            return _resolve(target, root)

        out = {k: _resolve(v, root) for k, v in node.items()
               if k != "nullable"}
        if node.get("nullable") and "type" in out:
            out["type"] = [out["type"], "null"]
        return out

    if isinstance(node, list):
        return [_resolve(item, root) for item in node]

    return node


@pytest.fixture(scope="session")
def schema_for(spec):
    """schema_for('/books/{id}', 'get', 200) -> the documented response schema."""
    def lookup(path: str, method: str, status: int):
        operation = spec["paths"][path][method]
        response = operation["responses"][str(status)]
        response = _resolve(response, spec)
        try:
            return response["content"]["application/json"]["schema"]
        except KeyError:
            return None
    return lookup
