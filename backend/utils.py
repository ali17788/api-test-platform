# -*- coding: utf-8 -*-
"""统一响应 & 通用工具"""
import json
from fastapi import HTTPException, Request


def ok(data=None, msg="success"):
    return {"code": 0, "msg": msg, "data": data}


def err(msg, code=1, status=400):
    return {"code": code, "msg": msg, "data": None}


def http_err(status: int, msg: str):
    raise HTTPException(status_code=status, detail=msg)


def jloads(s, default=None):
    try:
        return json.loads(s) if s else (default if default is not None else {})
    except Exception:
        return default if default is not None else {}


def jdumps(obj):
    return json.dumps(obj, ensure_ascii=False)


def get_user(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if not token:
        http_err(401, "未登录或登录已失效")
    row = None
    from db import q1, row_to_dict
    row = q1("SELECT u.* FROM tokens t JOIN users u ON u.id=t.user_id WHERE t.token=?", (token,))
    user = row_to_dict(row)
    if not user:
        http_err(401, "未登录或登录已失效")
    return user
