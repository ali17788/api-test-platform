# -*- coding: utf-8 -*-
"""认证模块：登录 / 登出 / 当前用户"""
import secrets
from fastapi import APIRouter, Request
from pydantic import BaseModel
import db as d
from utils import ok, http_err, get_user
from users import get_user_menus, get_role_name

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = ""
    password: str = ""


@router.post("/login")
def login(body: LoginBody):
    if not body.username or not body.password:
        http_err(400, "请输入用户名/密码")
    user = d.q1("SELECT * FROM users WHERE username=?", (body.username,))
    if not user or user["password"] != d.hash_pwd(body.password):
        http_err(400, "用户名或密码错误")
    token = secrets.token_hex(24)
    d.ex("INSERT INTO tokens(token,user_id) VALUES(?,?)", (token, user["id"]))
    d.op_log(user["username"], "登录", "用户登录成功")
    return ok({"token": token, "username": user["username"], "role": user["role"],
               "role_name": get_role_name(user), "menus": get_user_menus(user)})


@router.post("/logout")
def logout(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if token:
        d.ex("DELETE FROM tokens WHERE token=?", (token,))
    return ok(msg="已退出登录")


@router.get("/me")
def me(request: Request):
    user = get_user(request)
    return ok({"username": user["username"], "role": user["role"],
               "role_name": get_role_name(user), "menus": get_user_menus(user)})
