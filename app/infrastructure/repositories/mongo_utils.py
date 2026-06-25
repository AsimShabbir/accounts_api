from datetime import date, datetime
from decimal import Decimal
from typing import Any

from bson import ObjectId


def to_object_id(value: str) -> ObjectId:
    return ObjectId(value)


def serialize_document(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if doc is None:
        return None
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    return _convert_types(result)


def _convert_types(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    if isinstance(value, Decimal):
        return value
    if isinstance(value, dict):
        return {key: _convert_types(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_convert_types(item) for item in value]
    return value


def prepare_for_insert(data: dict[str, Any]) -> dict[str, Any]:
    payload = dict(data)
    payload.pop("id", None)
    return _prepare_value(payload)


def _prepare_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, dict):
        return {key: _prepare_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_prepare_value(item) for item in value]
    return value
