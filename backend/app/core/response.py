from typing import Any


def ok(data: Any = None, message: str = "OK", meta: dict | None = None) -> dict:
    resp: dict = {"success": True, "data": data, "message": message}
    if meta is not None:
        resp["meta"] = meta
    return resp
