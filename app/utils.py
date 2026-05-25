from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException


def row_to_dict(columns: list[str], row: tuple) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col, val in zip(columns, row):
        key = col.lower() if isinstance(col, str) else str(col).lower()
        out[key] = serialize_value(val)
    return out


def rows_to_list(cursor) -> list[dict[str, Any]]:
    columns = [d[0] for d in cursor.description]
    return [row_to_dict(columns, row) for row in cursor.fetchall()]


def serialize_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    return val


def oracle_error(exc: Exception) -> HTTPException:
    msg = str(exc)
    if hasattr(exc, "args") and exc.args:
        err = exc.args[0]
        if hasattr(err, "message"):
            msg = err.message
        elif isinstance(err, dict) and "message" in err:
            msg = err["message"]
    code = 400 if "ORA-2" in msg else 500
    return HTTPException(status_code=code, detail=msg)
