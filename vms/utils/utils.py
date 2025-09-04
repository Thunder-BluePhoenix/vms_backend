from __future__ import annotations
import base64
import json

import frappe
import requests

from typing import Any, Iterable, Optional


def send_request(url, payload, method="GET", headers=None):
    if payload is None:
        payload = {}
    if headers is None:
        headers = {}
    headers = {"Content-Type": "application/json", **headers}

    if method == "POST" or method == "PUT":
        response = requests.request(
            method,
            url,
            headers=headers,
            data=json.dumps(payload, default=str),
        )
    else:
        response = requests.request(method, url, headers=headers)
    return response

_DEFAULT_TRUTHY = {"1", "true", "yes", "y", "on"}
_DEFAULT_FALSEY = {"0", "false", "no", "n", "off"}


def to_bool(
    value: Any,
    *,
    default: bool = False,
    truthy: Optional[Iterable[str]] = None,
    falsey: Optional[Iterable[str]] = None,
) -> bool:
    """
    Coerce arbitrary values into a boolean.

    Handles common patterns like "1"/"0", "yes"/"no", "on"/"off", 1/0, True/False.
    - Strings are matched case-insensitively after stripping.
    - Non-string iterables/objects fallback to Python's `bool(value)` if not recognized.
    - `None` returns `default`.

    Args:
        value: The value to convert.
        default: Fallback when `value` is None or an unrecognized string.
        truthy: Optional custom set/iterable of truthy string tokens.
        falsey: Optional custom set/iterable of falsey string tokens.

    Examples:
        >>> to_bool(True)
        True
        >>> to_bool(" YES ")
        True
        >>> to_bool("0")
        False
        >>> to_bool(None, default=True)
        True
        >>> to_bool("custom", truthy={"custom"})
        True
    """
    if value is None:
        return default

    # Fast paths for native bool/int/float
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0

    # Strings: compare against token sets
    if isinstance(value, str):
        s = value.strip().lower()
        tset = set(truthy) if truthy is not None else _DEFAULT_TRUTHY
        fset = set(falsey) if falsey is not None else _DEFAULT_FALSEY
        if s in tset:
            return True
        if s in fset:
            return False
        return default

    # Fallback to Python truthiness for other types (lists, dicts, objects, etc.)
    return bool(value)


def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """
    Safely get an attribute or key from a Frappe Doc-like object or a dict.

    - If `obj` has the attribute, return it.
    - Else if `obj` is a dict, return dict[key].
    - Else return default.
    - Returns `default` if `obj` is None.

    Args:
        obj: The object or dict to query.
        key: The attribute/key name.
        default: Value to return if not found.

    Examples:
        >>> safe_get({"role": "Admin"}, "role")
        'Admin'
        >>> class Stage: role = "Manager"
        >>> safe_get(Stage(), "role")
        'Manager'
        >>> safe_get(None, "role", "N/A")
        'N/A'
    """
    if obj is None:
        return default

    # Frappe Doc / any Python object with attribute
    if hasattr(obj, key):
        return getattr(obj, key, default)

    # Dict-like
    if isinstance(obj, dict):
        return obj.get(key, default)

    return default
